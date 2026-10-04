-- =====================================================
-- SQL Schema: Excel Import System
-- Database: MariaDB
-- Table: documentos_dian
-- =====================================================

SET SQL_MODE = "NO_AUTO_VALUE_ON_ZERO";
SET time_zone = "+00:00";
SET NAMES utf8mb4;

-- Drop table if exists (for development/testing)
DROP TABLE IF EXISTS `documentos_dian`;

CREATE TABLE IF NOT EXISTS `documentos_dian` (
  `id` BIGINT(20) UNSIGNED NOT NULL AUTO_INCREMENT,
  `tipo_documento` VARCHAR(100) NOT NULL,
  `cufe_cude` VARCHAR(255) NOT NULL,
  `folio` VARCHAR(50) DEFAULT NULL,
  `prefijo` VARCHAR(20) DEFAULT NULL,
  `divisa` VARCHAR(10) DEFAULT NULL,
  `forma_pago` VARCHAR(50) DEFAULT NULL,
  `medio_pago` VARCHAR(50) DEFAULT NULL,
  `fecha_emision` DATE DEFAULT NULL,
  `fecha_recepcion` DATETIME DEFAULT NULL,
  `nit_emisor` BIGINT DEFAULT NULL,
  `nombre_emisor` VARCHAR(255) DEFAULT NULL,
  `nit_receptor` BIGINT DEFAULT NULL,
  `nombre_receptor` VARCHAR(255) DEFAULT NULL,
  `iva` DECIMAL(18,2) DEFAULT 0,
  `ica` DECIMAL(18,2) DEFAULT 0,
  `ic` DECIMAL(18,2) DEFAULT 0,
  `inc` DECIMAL(18,2) DEFAULT 0,
  `timbre` DECIMAL(18,2) DEFAULT 0,
  `inc_bolsas` DECIMAL(18,2) DEFAULT 0,
  `in_carbono` DECIMAL(18,2) DEFAULT 0,
  `in_combustibles` DECIMAL(18,2) DEFAULT 0,
  `ic_datos` DECIMAL(18,2) DEFAULT 0,
  `icl` DECIMAL(18,2) DEFAULT 0,
  `inpp` DECIMAL(18,2) DEFAULT 0,
  `ibua` DECIMAL(18,2) DEFAULT 0,
  `icui` DECIMAL(18,2) DEFAULT 0,
  `rete_iva` DECIMAL(18,2) DEFAULT 0,
  `rete_renta` DECIMAL(18,2) DEFAULT 0,
  `rete_ica` DECIMAL(18,2) DEFAULT 0,
  `total` DECIMAL(18,2) NOT NULL,
  `estado` VARCHAR(50) DEFAULT NULL,
  `grupo` VARCHAR(50) DEFAULT NULL,
  `archivo_origen` VARCHAR(255) DEFAULT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_documento` (`cufe_cude`),
  KEY `idx_cufe_cude` (`cufe_cude`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- =====================================================
-- Consolidado + Tabla Dinamica
-- =====================================================

DROP TABLE IF EXISTS `consolidado_movimientos`;
DROP TABLE IF EXISTS `terceros`;
DROP TABLE IF EXISTS `empresas`;

CREATE TABLE IF NOT EXISTS `empresas` (
  `id` BIGINT(20) UNSIGNED NOT NULL AUTO_INCREMENT,
  `nombre` VARCHAR(255) NOT NULL,
  `nit` VARCHAR(50) DEFAULT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_empresa_nombre_nit` (`nombre`, `nit`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS `terceros` (
  `id` BIGINT(20) UNSIGNED NOT NULL AUTO_INCREMENT,
  `nombre` VARCHAR(255) NOT NULL,
  `nit` VARCHAR(50) DEFAULT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_tercero_nombre_nit` (`nombre`, `nit`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS `consolidado_movimientos` (
  `id` BIGINT(20) UNSIGNED NOT NULL AUTO_INCREMENT,
  `empresa_id` BIGINT(20) UNSIGNED NOT NULL,
  `tercero_id` BIGINT(20) UNSIGNED NOT NULL,
  `fecha` DATE NOT NULL,
  `cuenta` VARCHAR(100) NOT NULL,
  `debito` DECIMAL(18,2) DEFAULT 0,
  `credito` DECIMAL(18,2) DEFAULT 0,
  `documento_origen` VARCHAR(255) DEFAULT NULL,
  `periodo` VARCHAR(50) DEFAULT NULL,
  `archivo_origen` VARCHAR(255) DEFAULT NULL,
  `fecha_importacion` TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  KEY `idx_consolidado_empresa` (`empresa_id`),
  KEY `idx_consolidado_tercero` (`tercero_id`),
  KEY `idx_consolidado_fecha` (`fecha`),
  KEY `idx_consolidado_cuenta` (`cuenta`),
  KEY `idx_consolidado_periodo` (`periodo`),
  CONSTRAINT `fk_consolidado_empresa` FOREIGN KEY (`empresa_id`) REFERENCES `empresas` (`id`),
  CONSTRAINT `fk_consolidado_tercero` FOREIGN KEY (`tercero_id`) REFERENCES `terceros` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
