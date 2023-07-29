from dotenv import load_dotenv
from datetime import datetime

import os, sys
import asyncio

import aiomysql
import asyncssh
import hashlib

load_dotenv()

db_polling_rate = int(os.getenv("DB_POLLING_RATE"))

db_info = {
    "db"            : os.getenv("DB_NAME"),
    "user"          : os.getenv("DB_USER"),
    "password"      : os.getenv("DB_PASSWORD"),
    "host"          : os.getenv("DB_HOST"),
    "port"          : 3306,
    "autocommit"    : True
}

ssh_info = {
    "username"      : os.getenv("SSH_USERNAME"),
    "client_keys"   : os.getenv("SSH_KEY_PATH"),
    "port"          : 22,
    "known_hosts"   : None
}

async def ssh_fetch_log(logid, instance_name, ip):
    try:
        async with  asyncssh.connect(**ssh_info, host=ip) as conn:
            command = f"/bin/bash server/fetch_log.sh {logid}"
            await conn.run(command)
            await asyncio.sleep(1)
            async with conn.start_sftp_client() as sftp:
                remote_path = f"server/logfile_{logid}.tar.gz"
                local_path  = f"logfiles/logfile_{logid}.tar.gz"
                await sftp.get(remotepaths=remote_path, localpath=local_path)
                return local_path
    except asyncssh.misc.PermissionDenied as e:
        print(f"Failed to SSH to {instance_name}: {e}")
        return None
    except asyncssh.sftp.SFTPNoSuchFile as e:
        print(f"Failed to retrieve logfile from {instance_name}: {e}")
        return None


async def generate_hash(file_path, algorithm="sha256"):
    # Initialize the hash object with the chosen algorithm
    hash_obj = hashlib.new(algorithm)

    # Open the file in binary read mode
    with open(file_path, "rb") as file:
        # Read the file in chunks to avoid memory issues with large files
        chunk_size = 4096
        while chunk := file.read(chunk_size):
            # Update the hash object with each chunk of data
            hash_obj.update(chunk)

    # Obtain the final hash value in hexadecimal format
    file_hash = hash_obj.hexdigest()
    return file_hash



async def connect_to_database():
    try:
        conn = await aiomysql.connect(**db_info) 
        return conn
    except aiomysql.Error as e:
        print(f"Error connecting to MariaDB Platform: {e}")
        sys.exit(1)


async def wait_for_sdr(ip, instance_name):
    # Send ip to database
    conn = await connect_to_database()
    try:
        cursor = await conn.cursor()
        sql = "UPDATE instances SET ip = %s WHERE instance_name = %s"
        data = (ip, instance_name)
        await cursor.execute(sql, data)
    except aiomysql.Error as e:
        print(f"Error sending ip to datebase: {e}")
        return "failed", None
    finally:
        conn.close()

    # wait for 180s
    max_retries = int(180/db_polling_rate)

    for i in range(max_retries):
        await asyncio.sleep(db_polling_rate)
        conn = await connect_to_database()
        try:
            cursor = await conn.cursor()

            sql = "SELECT started FROM bookings WHERE instance_name = %s LIMIT 1"
            data = (instance_name,)

            await cursor.execute(sql, data)
            started = await cursor.fetchone()

            if started[0] == 0: continue

            sql = "SELECT sdr_ip, sdr_port, sv_password, rcon_password FROM bookings WHERE instance_name = %s LIMIT 1"
            data = (instance_name,)

            await cursor.execute(sql, data)
            booking = await cursor.fetchone()

            return "success", booking
        
        except aiomysql.Error as e:
            print(f"Error sending ip to datebase: {e}")
            return "failed", None
        
        finally:
            conn.close()
    
    return "timeout", None


async def delete_booking_entry(instance_name):
    conn = await connect_to_database()
    try:
        cursor = await conn.cursor()
        sql = "DELETE FROM bookings WHERE instance_name = %s"
        data = (instance_name,)
        await cursor.execute(sql, data)
        return "success"
    except aiomysql.Error as e:
        print(f"Error querying database while sending details: {e}")
        return "failed"
    finally:
        conn.close()


async def book(userid, username, country):
    conn = await connect_to_database()

    try:
        cursor = await conn.cursor()

        # Check if the user has reached the booking limit
        sql = "SELECT * FROM bookings WHERE discord_id = %s"
        data = (userid,)
        await cursor.execute(sql, data)
        if cursor.rowcount > 0:
            return "user_limit", None, None
            
        # Find the first available server in the specified region
        sql = "SELECT * FROM instances WHERE country = %s AND offline = 0 AND booked = 0 LIMIT 1"
        data = (country,)
        await cursor.execute(sql, data)
        if cursor.rowcount == 0:
            return "capacity_limit", None, None
        
        instance = await cursor.fetchone()

        # Define variables
        instance_name = instance[0]
        instance_zone = instance[1]

        # Check if the user's discord_id exists in users table
        sql = "SELECT * FROM users WHERE discord_id = %s LIMIT 1"
        data = (userid,)
        await cursor.execute(sql, data)

        # Insert/Update user info to users table
        if cursor.rowcount == 0:
            sql = "INSERT INTO users (discord_alias, discord_id) VALUES (%s, %s)"
        else:
            sql = "UPDATE users SET discord_alias = %s WHERE discord_id = %s"

        data = (username, userid)
        await cursor.execute(sql, data)

        start_time = datetime.now()

        # Create entry in bookings table
        sql = "INSERT INTO bookings (discord_alias, discord_id, instance_name, instance_zone, start_time) VALUES (%s, %s, %s, %s, %s)"
        data = (username, userid, instance_name, instance_zone, start_time)
        await cursor.execute(sql, data)

        return "success", instance_name, instance_zone
    
    except aiomysql.Error as e:
        print(f"Error querying datebase while booking: {e}")
        return "failed", None, None
    
    finally:
        conn.close()


async def unbook(userid, username):
    conn = await connect_to_database()
    try:
        cursor = await conn.cursor()

        # Check if the user's discord_id exists in users table
        sql = "SELECT * FROM users WHERE discord_id = %s LIMIT 1"
        data = (userid,)
        await cursor.execute(sql, data)

        # Update user info to users table
        if cursor.rowcount == 1:
            sql = "UPDATE users SET discord_alias = %s WHERE discord_id = %s"
        data = (username, userid)
        await cursor.execute(sql, data)

        # Find the server booked by the user
        sql = "SELECT instance_name, instance_zone, ip, start_time FROM bookings WHERE discord_id = %s LIMIT 1"
        data = (userid,)
        await cursor.execute(sql, data)
        if cursor.rowcount == 0:
            return "none", None, None
        
        # Fetch booking info
        booking = await cursor.fetchone()

        # Define variables
        instance_name   = booking[0]
        instance_zone   = booking[1]
        ip              = booking[2]
        start_time      = booking[3]
        end_time        = datetime.now()

        # Create entry in history table
        sql = "INSERT INTO history (server, discord_id, discord_alias, start_time, end_time) VALUE (%s, %s, %s, %s, %s)"
        data = (instance_name, userid, username, start_time, end_time)
        await cursor.execute(sql, data)
        
        """
        # Fetch log tarball from instance
        logid = cursor.lastrowid
        logfile = await ssh_fetch_log(logid, instance_name, ip)
        if logfile is None:
            print(f"No logs for id={logid}")
            return "success", instance_name, instance_zone

        # Generate hash from file
        logfile_hash = await generate_hash(logfile)

        # Update hash to history table
        sql = "UPDATE history SET logfile_hash = %s WHERE id = %s"
        data = (logfile_hash, logid)
        await cursor.execute(sql, data)
        """
        
        return "success", instance_name, instance_zone

    except aiomysql.Error as e:
        print(f"Error querying datebase while booking: {e}")
        return "failed", None, None