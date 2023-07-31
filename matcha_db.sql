-- MariaDB dump 10.19-11.0.2-MariaDB, for debian-linux-gnu (x86_64)
--
-- Host: localhost    Database: matcha_db
-- ------------------------------------------------------
-- Server version	11.0.2-MariaDB-1:11.0.2+maria~ubu2304

/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!40101 SET NAMES utf8mb4 */;
/*!40103 SET @OLD_TIME_ZONE=@@TIME_ZONE */;
/*!40103 SET TIME_ZONE='+00:00' */;
/*!40014 SET @OLD_UNIQUE_CHECKS=@@UNIQUE_CHECKS, UNIQUE_CHECKS=0 */;
/*!40014 SET @OLD_FOREIGN_KEY_CHECKS=@@FOREIGN_KEY_CHECKS, FOREIGN_KEY_CHECKS=0 */;
/*!40101 SET @OLD_SQL_MODE=@@SQL_MODE, SQL_MODE='NO_AUTO_VALUE_ON_ZERO' */;
/*!40111 SET @OLD_SQL_NOTES=@@SQL_NOTES, SQL_NOTES=0 */;

--
-- Table structure for table `bookings`
--

DROP TABLE IF EXISTS `bookings`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `bookings` (
  `instance_name` varchar(40) NOT NULL,
  `instance_zone` varchar(32) NOT NULL,
  `ip` char(16) NOT NULL DEFAULT '0.0.0.0',
  `sdr_ip` char(16) DEFAULT NULL,
  `sdr_port` int(5) unsigned DEFAULT NULL,
  `sv_password` varchar(32) DEFAULT NULL,
  `rcon_password` varchar(32) DEFAULT NULL,
  `started` tinyint(1) NOT NULL DEFAULT 0,
  `afk` tinyint(1) unsigned NOT NULL DEFAULT 0,
  `discord_id` bigint(20) unsigned NOT NULL,
  `discord_alias` varchar(40) NOT NULL,
  `start_time` datetime NOT NULL,
  PRIMARY KEY (`instance_name`) USING BTREE,
  KEY `instance_info_bookings` (`instance_name`,`instance_zone`,`ip`) USING BTREE,
  KEY `discord_info_bookings` (`discord_id`,`discord_alias`) USING BTREE,
  CONSTRAINT `discord_info_bookings` FOREIGN KEY (`discord_id`, `discord_alias`) REFERENCES `users` (`discord_id`, `discord_alias`) ON DELETE NO ACTION ON UPDATE CASCADE,
  CONSTRAINT `instance_info_bookings` FOREIGN KEY (`instance_name`, `instance_zone`, `ip`) REFERENCES `instances` (`instance_name`, `instance_zone`, `ip`) ON DELETE NO ACTION ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;
/*!40101 SET character_set_client = @saved_cs_client */;
/*!50003 SET @saved_cs_client      = @@character_set_client */ ;
/*!50003 SET @saved_cs_results     = @@character_set_results */ ;
/*!50003 SET @saved_col_connection = @@collation_connection */ ;
/*!50003 SET character_set_client  = utf8mb4 */ ;
/*!50003 SET character_set_results = utf8mb4 */ ;
/*!50003 SET collation_connection  = utf8mb4_general_ci */ ;
/*!50003 SET @saved_sql_mode       = @@sql_mode */ ;
/*!50003 SET sql_mode              = 'STRICT_TRANS_TABLES,ERROR_FOR_DIVISION_BY_ZERO,NO_AUTO_CREATE_USER,NO_ENGINE_SUBSTITUTION' */ ;
DELIMITER ;;
/*!50003 CREATE*/ /*!50017 DEFINER=`aqua_hopps`@`%`*/ /*!50003 TRIGGER `bookings_after_insert` AFTER INSERT ON `bookings` FOR EACH ROW BEGIN
	UPDATE instances
	SET booked = 1
	WHERE instance_name = NEW.instance_name;
END */;;
DELIMITER ;
/*!50003 SET sql_mode              = @saved_sql_mode */ ;
/*!50003 SET character_set_client  = @saved_cs_client */ ;
/*!50003 SET character_set_results = @saved_cs_results */ ;
/*!50003 SET collation_connection  = @saved_col_connection */ ;
/*!50003 SET @saved_cs_client      = @@character_set_client */ ;
/*!50003 SET @saved_cs_results     = @@character_set_results */ ;
/*!50003 SET @saved_col_connection = @@collation_connection */ ;
/*!50003 SET character_set_client  = utf8mb4 */ ;
/*!50003 SET character_set_results = utf8mb4 */ ;
/*!50003 SET collation_connection  = utf8mb4_general_ci */ ;
/*!50003 SET @saved_sql_mode       = @@sql_mode */ ;
/*!50003 SET sql_mode              = 'STRICT_TRANS_TABLES,ERROR_FOR_DIVISION_BY_ZERO,NO_AUTO_CREATE_USER,NO_ENGINE_SUBSTITUTION' */ ;
DELIMITER ;;
/*!50003 CREATE*/ /*!50017 DEFINER=`aqua_hopps`@`%`*/ /*!50003 TRIGGER `bookings_after_delete` AFTER DELETE ON `bookings` FOR EACH ROW BEGIN
	UPDATE instances
	SET
		booked = DEFAULT,
		ip = DEFAULT
	WHERE instance_name = OLD.instance_name;
END */;;
DELIMITER ;
/*!50003 SET sql_mode              = @saved_sql_mode */ ;
/*!50003 SET character_set_client  = @saved_cs_client */ ;
/*!50003 SET character_set_results = @saved_cs_results */ ;
/*!50003 SET collation_connection  = @saved_col_connection */ ;

--
-- Table structure for table `history`
--

DROP TABLE IF EXISTS `history`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `history` (
  `id` int(10) unsigned NOT NULL AUTO_INCREMENT,
  `server` varchar(32) NOT NULL,
  `discord_id` bigint(20) unsigned NOT NULL,
  `discord_alias` varchar(40) NOT NULL,
  `start_time` datetime NOT NULL,
  `end_time` datetime NOT NULL,
  `duration` time DEFAULT timediff(`end_time`,`start_time`),
  `logfile_hash` char(64) DEFAULT NULL,
  PRIMARY KEY (`id`) USING BTREE,
  KEY `discord_info_history` (`discord_id`,`discord_alias`) USING BTREE,
  CONSTRAINT `discord_info_history` FOREIGN KEY (`discord_id`, `discord_alias`) REFERENCES `users` (`discord_id`, `discord_alias`) ON DELETE NO ACTION ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;
/*!40101 SET character_set_client = @saved_cs_client */;
/*!50003 SET @saved_cs_client      = @@character_set_client */ ;
/*!50003 SET @saved_cs_results     = @@character_set_results */ ;
/*!50003 SET @saved_col_connection = @@collation_connection */ ;
/*!50003 SET character_set_client  = utf8mb4 */ ;
/*!50003 SET character_set_results = utf8mb4 */ ;
/*!50003 SET collation_connection  = utf8mb4_general_ci */ ;
/*!50003 SET @saved_sql_mode       = @@sql_mode */ ;
/*!50003 SET sql_mode              = 'STRICT_TRANS_TABLES,ERROR_FOR_DIVISION_BY_ZERO,NO_AUTO_CREATE_USER,NO_ENGINE_SUBSTITUTION' */ ;
DELIMITER ;;
/*!50003 CREATE*/ /*!50017 DEFINER=`aqua_hopps`@`%`*/ /*!50003 TRIGGER `history_after_insert` AFTER INSERT ON `history` FOR EACH ROW BEGIN
	UPDATE users
	SET
		book_count = book_count + 1,
		total_duration =
			SEC_TO_TIME(TIME_TO_SEC(total_duration) + TIME_TO_SEC(NEW.duration))
	WHERE discord_id = NEW.discord_id;
END */;;
DELIMITER ;
/*!50003 SET sql_mode              = @saved_sql_mode */ ;
/*!50003 SET character_set_client  = @saved_cs_client */ ;
/*!50003 SET character_set_results = @saved_cs_results */ ;
/*!50003 SET collation_connection  = @saved_col_connection */ ;
/*!50003 SET @saved_cs_client      = @@character_set_client */ ;
/*!50003 SET @saved_cs_results     = @@character_set_results */ ;
/*!50003 SET @saved_col_connection = @@collation_connection */ ;
/*!50003 SET character_set_client  = utf8mb4 */ ;
/*!50003 SET character_set_results = utf8mb4 */ ;
/*!50003 SET collation_connection  = utf8mb4_general_ci */ ;
/*!50003 SET @saved_sql_mode       = @@sql_mode */ ;
/*!50003 SET sql_mode              = 'STRICT_TRANS_TABLES,ERROR_FOR_DIVISION_BY_ZERO,NO_AUTO_CREATE_USER,NO_ENGINE_SUBSTITUTION' */ ;
DELIMITER ;;
/*!50003 CREATE*/ /*!50017 DEFINER=`aqua_hopps`@`%`*/ /*!50003 TRIGGER `history_after_delete` AFTER DELETE ON `history` FOR EACH ROW BEGIN
	UPDATE users
	SET
		book_count = book_count - 1,
		total_duration = 
			SEC_TO_TIME(TIME_TO_SEC(total_duration) - TIME_TO_SEC(OLD.duration))
	WHERE discord_id = OLD.discord_id;
END */;;
DELIMITER ;
/*!50003 SET sql_mode              = @saved_sql_mode */ ;
/*!50003 SET character_set_client  = @saved_cs_client */ ;
/*!50003 SET character_set_results = @saved_cs_results */ ;
/*!50003 SET collation_connection  = @saved_col_connection */ ;

--
-- Table structure for table `instances`
--

DROP TABLE IF EXISTS `instances`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `instances` (
  `instance_name` varchar(32) NOT NULL,
  `instance_zone` varchar(32) NOT NULL,
  `ip` char(16) NOT NULL DEFAULT '0.0.0.0',
  `region` varchar(32) NOT NULL,
  `country` char(3) NOT NULL,
  `booked` tinyint(1) unsigned NOT NULL DEFAULT 0,
  `offline` tinyint(1) unsigned NOT NULL DEFAULT 0 COMMENT 'maintenance',
  PRIMARY KEY (`instance_name`) USING BTREE,
  KEY `instance` (`instance_name`,`instance_zone`,`ip`) USING BTREE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `users`
--

DROP TABLE IF EXISTS `users`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `users` (
  `discord_id` bigint(20) unsigned NOT NULL,
  `discord_alias` varchar(40) NOT NULL,
  `steam_id` bigint(20) unsigned DEFAULT NULL,
  `steam_alias` varchar(40) DEFAULT NULL,
  `book_count` int(10) unsigned NOT NULL DEFAULT 0,
  `total_duration` time NOT NULL DEFAULT '00:00:00',
  PRIMARY KEY (`discord_id`),
  KEY `discord` (`discord_id`,`discord_alias`) USING BTREE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;
/*!40101 SET character_set_client = @saved_cs_client */;
/*!40103 SET TIME_ZONE=@OLD_TIME_ZONE */;

/*!40101 SET SQL_MODE=@OLD_SQL_MODE */;
/*!40014 SET FOREIGN_KEY_CHECKS=@OLD_FOREIGN_KEY_CHECKS */;
/*!40014 SET UNIQUE_CHECKS=@OLD_UNIQUE_CHECKS */;
/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
/*!40111 SET SQL_NOTES=@OLD_SQL_NOTES */;

-- Dump completed on 2023-07-31 14:08:31
