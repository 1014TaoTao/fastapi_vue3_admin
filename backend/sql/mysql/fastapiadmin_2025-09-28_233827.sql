-- MySQL dump 10.13  Distrib 8.4.3, for macos14.5 (arm64)
--
-- Host: 127.0.0.1    Database: fastapiadmin
-- ------------------------------------------------------
-- Server version	8.4.3

/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!50503 SET NAMES utf8mb4 */;
/*!40103 SET @OLD_TIME_ZONE=@@TIME_ZONE */;
/*!40103 SET TIME_ZONE='+00:00' */;
/*!40014 SET @OLD_UNIQUE_CHECKS=@@UNIQUE_CHECKS, UNIQUE_CHECKS=0 */;
/*!40014 SET @OLD_FOREIGN_KEY_CHECKS=@@FOREIGN_KEY_CHECKS, FOREIGN_KEY_CHECKS=0 */;
/*!40101 SET @OLD_SQL_MODE=@@SQL_MODE, SQL_MODE='NO_AUTO_VALUE_ON_ZERO' */;
/*!40111 SET @OLD_SQL_NOTES=@@SQL_NOTES, SQL_NOTES=0 */;

--
-- Table structure for table `ai_mcp`
--

DROP TABLE IF EXISTS `ai_mcp`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `ai_mcp` (
  `name` varchar(50) NOT NULL COMMENT 'MCP 名称',
  `type` int NOT NULL COMMENT 'MCP 类型（0:stdio 1:sse）',
  `url` varchar(255) DEFAULT NULL COMMENT '远程 SSE 地址',
  `command` varchar(255) DEFAULT NULL COMMENT 'MCP 命令',
  `args` varchar(255) DEFAULT NULL COMMENT 'MCP 命令参数',
  `env` json DEFAULT NULL COMMENT 'MCP 环境变量',
  `creator_id` int DEFAULT NULL COMMENT '创建人ID',
  `id` int NOT NULL AUTO_INCREMENT COMMENT '主键ID',
  `description` text COMMENT '备注/描述',
  `created_at` datetime DEFAULT NULL COMMENT '创建时间',
  `updated_at` datetime DEFAULT NULL COMMENT '更新时间',
  PRIMARY KEY (`id`),
  UNIQUE KEY `name` (`name`),
  KEY `ix_ai_mcp_creator_id` (`creator_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci COMMENT='MCP 服务器表';
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `ai_mcp`
--

/*!40000 ALTER TABLE `ai_mcp` DISABLE KEYS */;
/*!40000 ALTER TABLE `ai_mcp` ENABLE KEYS */;

--
-- Table structure for table `application_myapp`
--

DROP TABLE IF EXISTS `application_myapp`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `application_myapp` (
  `name` varchar(64) NOT NULL COMMENT '应用名称',
  `status` tinyint(1) NOT NULL COMMENT '是否启用(True:启用 False:禁用)',
  `access_url` varchar(500) NOT NULL COMMENT '访问地址',
  `icon_url` varchar(300) DEFAULT NULL COMMENT '应用图标URL',
  `creator_id` int DEFAULT NULL COMMENT '创建人ID',
  `id` int NOT NULL AUTO_INCREMENT COMMENT '主键ID',
  `description` text COMMENT '备注/描述',
  `created_at` datetime DEFAULT NULL COMMENT '创建时间',
  `updated_at` datetime DEFAULT NULL COMMENT '更新时间',
  PRIMARY KEY (`id`),
  UNIQUE KEY `name` (`name`),
  KEY `ix_application_myapp_creator_id` (`creator_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci COMMENT='应用系统表';
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `application_myapp`
--

/*!40000 ALTER TABLE `application_myapp` DISABLE KEYS */;
/*!40000 ALTER TABLE `application_myapp` ENABLE KEYS */;

--
-- Table structure for table `example_demo`
--

DROP TABLE IF EXISTS `example_demo`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `example_demo` (
  `name` varchar(64) DEFAULT NULL COMMENT '名称',
  `status` tinyint(1) NOT NULL COMMENT '是否启用(True:启用 False:禁用)',
  `creator_id` int DEFAULT NULL COMMENT '创建人ID',
  `id` int NOT NULL AUTO_INCREMENT COMMENT '主键ID',
  `description` text COMMENT '备注/描述',
  `created_at` datetime DEFAULT NULL COMMENT '创建时间',
  `updated_at` datetime DEFAULT NULL COMMENT '更新时间',
  PRIMARY KEY (`id`),
  KEY `ix_example_demo_creator_id` (`creator_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci COMMENT='示例表';
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `example_demo`
--

/*!40000 ALTER TABLE `example_demo` DISABLE KEYS */;
/*!40000 ALTER TABLE `example_demo` ENABLE KEYS */;

--
-- Table structure for table `gen_table`
--

DROP TABLE IF EXISTS `gen_table`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `gen_table` (
  `table_name` varchar(200) DEFAULT NULL COMMENT '表名称',
  `table_comment` varchar(500) DEFAULT NULL COMMENT '表描述',
  `sub_table_name` varchar(64) DEFAULT NULL COMMENT '关联子表的表名',
  `sub_table_fk_name` varchar(64) DEFAULT NULL COMMENT '子表关联的外键名',
  `class_name` varchar(100) DEFAULT NULL COMMENT '实体类名称',
  `tpl_category` varchar(200) DEFAULT NULL COMMENT '使用的模板（crud单表操作 tree树表操作）',
  `tpl_web_type` varchar(30) DEFAULT NULL COMMENT '前端模板类型（element-ui模版 element-plus模版）',
  `package_name` varchar(100) DEFAULT NULL COMMENT '生成包路径',
  `module_name` varchar(30) DEFAULT NULL COMMENT '生成模块名',
  `business_name` varchar(30) DEFAULT NULL COMMENT '生成业务名',
  `function_name` varchar(100) DEFAULT NULL COMMENT '生成功能名',
  `function_author` varchar(100) DEFAULT NULL COMMENT '生成功能作者',
  `gen_type` varchar(1) DEFAULT NULL COMMENT '生成代码方式（0zip压缩包 1自定义路径）',
  `gen_path` varchar(200) DEFAULT NULL COMMENT '生成路径（不填默认项目路径）',
  `options` varchar(1000) DEFAULT NULL COMMENT '其它生成选项',
  `creator_id` int DEFAULT NULL COMMENT '创建人ID',
  `id` int NOT NULL AUTO_INCREMENT COMMENT '主键ID',
  `description` text COMMENT '备注/描述',
  `created_at` datetime DEFAULT NULL COMMENT '创建时间',
  `updated_at` datetime DEFAULT NULL COMMENT '更新时间',
  PRIMARY KEY (`id`),
  KEY `ix_gen_table_creator_id` (`creator_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci COMMENT='代码生成表';
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `gen_table`
--

/*!40000 ALTER TABLE `gen_table` DISABLE KEYS */;
/*!40000 ALTER TABLE `gen_table` ENABLE KEYS */;

--
-- Table structure for table `gen_table_column`
--

DROP TABLE IF EXISTS `gen_table_column`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `gen_table_column` (
  `column_name` varchar(200) DEFAULT NULL COMMENT '列名称',
  `column_comment` varchar(500) DEFAULT NULL COMMENT '列描述',
  `column_type` varchar(100) DEFAULT NULL COMMENT '列类型',
  `python_type` varchar(500) DEFAULT NULL COMMENT 'PYTHON类型',
  `python_field` varchar(200) DEFAULT NULL COMMENT 'PYTHON字段名',
  `is_pk` varchar(1) DEFAULT NULL COMMENT '是否主键（1是）',
  `is_increment` varchar(1) DEFAULT NULL COMMENT '是否自增（1是）',
  `is_required` varchar(1) DEFAULT NULL COMMENT '是否必填（1是）',
  `is_unique` varchar(1) DEFAULT NULL COMMENT '是否唯一（1是）',
  `is_insert` varchar(1) DEFAULT NULL COMMENT '是否为插入字段（1是）',
  `is_edit` varchar(1) DEFAULT NULL COMMENT '是否编辑字段（1是）',
  `is_list` varchar(1) DEFAULT NULL COMMENT '是否列表字段（1是）',
  `is_query` varchar(1) DEFAULT NULL COMMENT '是否查询字段（1是）',
  `query_type` varchar(200) DEFAULT NULL COMMENT '查询方式（等于、不等于、大于、小于、范围）',
  `html_type` varchar(200) DEFAULT NULL COMMENT '显示类型（文本框、文本域、下拉框、复选框、单选框、日期控件）',
  `dict_type` varchar(200) DEFAULT NULL COMMENT '字典类型',
  `sort` int DEFAULT NULL COMMENT '排序',
  `table_id` int DEFAULT NULL COMMENT '归属表编号',
  `creator_id` int DEFAULT NULL COMMENT '创建人ID',
  `id` int NOT NULL AUTO_INCREMENT COMMENT '主键ID',
  `description` text COMMENT '备注/描述',
  `created_at` datetime DEFAULT NULL COMMENT '创建时间',
  `updated_at` datetime DEFAULT NULL COMMENT '更新时间',
  PRIMARY KEY (`id`),
  KEY `table_id` (`table_id`),
  KEY `ix_gen_table_column_creator_id` (`creator_id`),
  CONSTRAINT `gen_table_column_ibfk_1` FOREIGN KEY (`table_id`) REFERENCES `gen_table` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci COMMENT='代码生成表字段';
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `gen_table_column`
--

/*!40000 ALTER TABLE `gen_table_column` DISABLE KEYS */;
/*!40000 ALTER TABLE `gen_table_column` ENABLE KEYS */;

--
-- Table structure for table `monitor_job`
--

DROP TABLE IF EXISTS `monitor_job`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `monitor_job` (
  `name` varchar(64) DEFAULT NULL COMMENT '任务名称',
  `jobstore` varchar(64) DEFAULT NULL COMMENT '存储器',
  `executor` varchar(64) DEFAULT NULL COMMENT '执行器:将运行此作业的执行程序的名称',
  `trigger` varchar(64) NOT NULL COMMENT '触发器:控制此作业计划的 trigger 对象',
  `trigger_args` text COMMENT '触发器参数',
  `func` text NOT NULL COMMENT '任务函数',
  `args` text COMMENT '位置参数',
  `kwargs` text COMMENT '关键字参数',
  `coalesce` tinyint(1) DEFAULT NULL COMMENT '是否合并运行:是否在多个运行时间到期时仅运行作业一次',
  `max_instances` int DEFAULT NULL COMMENT '最大实例数:允许的最大并发执行实例数 工作',
  `start_date` varchar(64) DEFAULT NULL COMMENT '开始时间',
  `end_date` varchar(64) DEFAULT NULL COMMENT '结束时间',
  `status` tinyint(1) NOT NULL COMMENT '是否启用(True:启用 False:禁用)',
  `creator_id` int DEFAULT NULL COMMENT '创建人ID',
  `id` int NOT NULL AUTO_INCREMENT COMMENT '主键ID',
  `description` text COMMENT '备注/描述',
  `created_at` datetime DEFAULT NULL COMMENT '创建时间',
  `updated_at` datetime DEFAULT NULL COMMENT '更新时间',
  PRIMARY KEY (`id`),
  KEY `ix_monitor_job_creator_id` (`creator_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci COMMENT='定时任务调度表';
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `monitor_job`
--

/*!40000 ALTER TABLE `monitor_job` DISABLE KEYS */;
/*!40000 ALTER TABLE `monitor_job` ENABLE KEYS */;

--
-- Table structure for table `monitor_job_log`
--

DROP TABLE IF EXISTS `monitor_job_log`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `monitor_job_log` (
  `id` int NOT NULL AUTO_INCREMENT COMMENT '主键ID',
  `job_name` varchar(64) NOT NULL COMMENT '任务名称',
  `job_group` varchar(64) NOT NULL COMMENT '任务组名',
  `job_executor` varchar(64) NOT NULL COMMENT '任务执行器',
  `invoke_target` varchar(500) NOT NULL COMMENT '调用目标字符串',
  `job_args` varchar(255) DEFAULT NULL COMMENT '位置参数',
  `job_kwargs` varchar(255) DEFAULT NULL COMMENT '关键字参数',
  `job_trigger` varchar(255) DEFAULT NULL COMMENT '任务触发器',
  `job_message` varchar(500) DEFAULT NULL COMMENT '日志信息',
  `exception_info` varchar(2000) DEFAULT NULL COMMENT '异常信息',
  `job_id` int DEFAULT NULL COMMENT '任务ID',
  PRIMARY KEY (`id`),
  KEY `job_id` (`job_id`),
  CONSTRAINT `monitor_job_log_ibfk_1` FOREIGN KEY (`job_id`) REFERENCES `monitor_job` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci COMMENT='定时任务调度日志表';
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `monitor_job_log`
--

/*!40000 ALTER TABLE `monitor_job_log` DISABLE KEYS */;
/*!40000 ALTER TABLE `monitor_job_log` ENABLE KEYS */;

--
-- Table structure for table `system_dept`
--

DROP TABLE IF EXISTS `system_dept`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `system_dept` (
  `id` int NOT NULL AUTO_INCREMENT COMMENT '主键ID',
  `name` varchar(40) NOT NULL COMMENT '部门名称',
  `order` int NOT NULL COMMENT '显示排序',
  `code` varchar(20) DEFAULT NULL COMMENT '部门编码',
  `status` tinyint(1) NOT NULL COMMENT '是否启用(True:启用 False:禁用)',
  `parent_id` int DEFAULT NULL COMMENT '父级部门ID',
  `description` text COMMENT '备注/描述',
  `created_at` datetime DEFAULT NULL COMMENT '创建时间',
  `updated_at` datetime DEFAULT NULL COMMENT '更新时间',
  PRIMARY KEY (`id`),
  UNIQUE KEY `name` (`name`),
  UNIQUE KEY `code` (`code`),
  KEY `ix_system_dept_parent_id` (`parent_id`),
  CONSTRAINT `system_dept_ibfk_1` FOREIGN KEY (`parent_id`) REFERENCES `system_dept` (`id`) ON DELETE SET NULL ON UPDATE CASCADE
) ENGINE=InnoDB AUTO_INCREMENT=8 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci COMMENT='部门表';
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `system_dept`
--

/*!40000 ALTER TABLE `system_dept` DISABLE KEYS */;
INSERT INTO `system_dept` VALUES (1,'集团总公司',1,'GROUP001',1,NULL,'集团总公司','2025-09-28 23:38:17','2025-09-28 23:38:17'),(2,'北京分公司',1,'BJ001',1,1,'北京分公司','2025-09-28 23:38:17','2025-09-28 23:38:17'),(3,'上海分公司',2,'SH001',1,1,'上海分公司','2025-09-28 23:38:17','2025-09-28 23:38:17'),(4,'技术部',1,'TECH001',1,2,'技术部','2025-09-28 23:38:17','2025-09-28 23:38:17'),(5,'销售部',2,'SALES001',1,2,'销售部','2025-09-28 23:38:17','2025-09-28 23:38:17'),(6,'市场部',1,'MARKET001',1,3,'市场部','2025-09-28 23:38:17','2025-09-28 23:38:17'),(7,'人事部',2,'HR001',1,3,'人事部','2025-09-28 23:38:17','2025-09-28 23:38:17');
/*!40000 ALTER TABLE `system_dept` ENABLE KEYS */;

--
-- Table structure for table `system_dict_data`
--

DROP TABLE IF EXISTS `system_dict_data`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `system_dict_data` (
  `dict_sort` int NOT NULL COMMENT '字典排序',
  `dict_label` varchar(100) NOT NULL COMMENT '字典标签',
  `dict_value` varchar(100) NOT NULL COMMENT '字典键值',
  `dict_type` varchar(100) NOT NULL COMMENT '字典类型',
  `status` tinyint(1) NOT NULL COMMENT '是否启用(True:启用 False:禁用)',
  `css_class` varchar(100) DEFAULT NULL COMMENT '样式属性（其他样式扩展）',
  `list_class` varchar(100) DEFAULT NULL COMMENT '表格回显样式',
  `is_default` tinyint(1) NOT NULL COMMENT '是否默认（True是 False否）',
  `dict_type_id` int DEFAULT NULL COMMENT '字典类型ID',
  `creator_id` int DEFAULT NULL COMMENT '创建人ID',
  `id` int NOT NULL AUTO_INCREMENT COMMENT '主键ID',
  `description` text COMMENT '备注/描述',
  `created_at` datetime DEFAULT NULL COMMENT '创建时间',
  `updated_at` datetime DEFAULT NULL COMMENT '更新时间',
  PRIMARY KEY (`id`),
  KEY `dict_type_id` (`dict_type_id`),
  KEY `ix_system_dict_data_creator_id` (`creator_id`),
  CONSTRAINT `system_dict_data_ibfk_1` FOREIGN KEY (`dict_type_id`) REFERENCES `system_dict_type` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=35 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci COMMENT='字典数据表';
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `system_dict_data`
--

/*!40000 ALTER TABLE `system_dict_data` DISABLE KEYS */;
INSERT INTO `system_dict_data` VALUES (1,'男','0','sys_user_sex',1,'blue',NULL,1,NULL,1,1,'性别男','2025-09-28 23:38:17','2025-09-28 23:38:17'),(2,'女','1','sys_user_sex',1,'pink',NULL,0,NULL,1,2,'性别女','2025-09-28 23:38:17','2025-09-28 23:38:17'),(3,'未知','2','sys_user_sex',1,'red',NULL,0,NULL,1,3,'性别未知','2025-09-28 23:38:17','2025-09-28 23:38:17'),(1,'启用','1','sys_common_status',1,'','primary',0,NULL,1,4,'启用状态','2025-09-28 23:38:17','2025-09-28 23:38:17'),(2,'停用','0','sys_common_status',1,'','danger',0,NULL,1,5,'停用状态','2025-09-28 23:38:17','2025-09-28 23:38:17'),(1,'是','1','sys_yes_no',1,'','primary',1,NULL,1,6,'是','2025-09-28 23:38:17','2025-09-28 23:38:17'),(2,'否','0','sys_yes_no',1,'','danger',0,NULL,1,7,'否','2025-09-28 23:38:17','2025-09-28 23:38:17'),(99,'其他','0','sys_oper_type',1,'','info',0,NULL,1,8,'其他操作','2025-09-28 23:38:17','2025-09-28 23:38:17'),(1,'新增','1','sys_oper_type',1,'','info',0,NULL,1,9,'新增操作','2025-09-28 23:38:17','2025-09-28 23:38:17'),(2,'修改','2','sys_oper_type',1,'','info',0,NULL,1,10,'修改操作','2025-09-28 23:38:17','2025-09-28 23:38:17'),(3,'删除','3','sys_oper_type',1,'','danger',0,NULL,1,11,'删除操作','2025-09-28 23:38:17','2025-09-28 23:38:17'),(4,'分配权限','4','sys_oper_type',1,'','primary',0,NULL,1,12,'授权操作','2025-09-28 23:38:17','2025-09-28 23:38:17'),(5,'导出','5','sys_oper_type',1,'','warning',0,NULL,1,13,'导出操作','2025-09-28 23:38:17','2025-09-28 23:38:17'),(6,'导入','6','sys_oper_type',1,'','warning',0,NULL,1,14,'导入操作','2025-09-28 23:38:17','2025-09-28 23:38:17'),(7,'强退','7','sys_oper_type',1,'','danger',0,NULL,1,15,'强退操作','2025-09-28 23:38:17','2025-09-28 23:38:17'),(8,'生成代码','8','sys_oper_type',1,'','warning',0,NULL,1,16,'生成操作','2025-09-28 23:38:17','2025-09-28 23:38:17'),(9,'清空数据','9','sys_oper_type',1,'','danger',0,NULL,1,17,'清空操作','2025-09-28 23:38:17','2025-09-28 23:38:17'),(1,'通知','1','sys_notice_type',1,'blue','warning',1,NULL,1,18,'通知','2025-09-28 23:38:17','2025-09-28 23:38:17'),(2,'公告','2','sys_notice_type',1,'orange','success',0,NULL,1,19,'公告','2025-09-28 23:38:17','2025-09-28 23:38:17'),(1,'默认(Memory)','default','sys_job_store',1,'',NULL,1,NULL,1,20,'默认分组','2025-09-28 23:38:17','2025-09-28 23:38:17'),(2,'数据库(Sqlalchemy)','sqlalchemy','sys_job_store',1,'',NULL,0,NULL,1,21,'数据库分组','2025-09-28 23:38:17','2025-09-28 23:38:17'),(3,'数据库(Redis)','redis','sys_job_store',1,'',NULL,0,NULL,1,22,'reids分组','2025-09-28 23:38:17','2025-09-28 23:38:17'),(1,'线程池','default','sys_job_executor',1,'',NULL,0,NULL,1,23,'线程池','2025-09-28 23:38:17','2025-09-28 23:38:17'),(2,'进程池','processpool','sys_job_executor',1,'',NULL,0,NULL,1,24,'进程池','2025-09-28 23:38:17','2025-09-28 23:38:17'),(1,'演示函数','scheduler_test.job','sys_job_function',1,'',NULL,1,NULL,1,25,'演示函数','2025-09-28 23:38:17','2025-09-28 23:38:17'),(1,'指定日期(date)','date','sys_job_trigger',1,'',NULL,1,NULL,1,26,'指定日期任务触发器','2025-09-28 23:38:17','2025-09-28 23:38:17'),(2,'间隔触发器(interval)','interval','sys_job_trigger',1,'',NULL,0,NULL,1,27,'间隔触发器任务触发器','2025-09-28 23:38:17','2025-09-28 23:38:17'),(3,'cron表达式','cron','sys_job_trigger',1,'',NULL,0,NULL,1,28,'间隔触发器任务触发器','2025-09-28 23:38:17','2025-09-28 23:38:17'),(1,'默认(default)','default','sys_list_class',1,'',NULL,1,NULL,1,29,'默认表格回显样式','2025-09-28 23:38:17','2025-09-28 23:38:17'),(2,'主要(primary)','primary','sys_list_class',1,'',NULL,0,NULL,1,30,'主要表格回显样式','2025-09-28 23:38:17','2025-09-28 23:38:17'),(3,'成功(success)','success','sys_list_class',1,'',NULL,0,NULL,1,31,'成功表格回显样式','2025-09-28 23:38:17','2025-09-28 23:38:17'),(4,'信息(info)','info','sys_list_class',1,'',NULL,0,NULL,1,32,'信息表格回显样式','2025-09-28 23:38:17','2025-09-28 23:38:17'),(5,'警告(warning)','warning','sys_list_class',1,'',NULL,0,NULL,1,33,'警告表格回显样式','2025-09-28 23:38:17','2025-09-28 23:38:17'),(6,'危险(danger)','danger','sys_list_class',1,'',NULL,0,NULL,1,34,'危险表格回显样式','2025-09-28 23:38:17','2025-09-28 23:38:17');
/*!40000 ALTER TABLE `system_dict_data` ENABLE KEYS */;

--
-- Table structure for table `system_dict_type`
--

DROP TABLE IF EXISTS `system_dict_type`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `system_dict_type` (
  `dict_name` varchar(100) NOT NULL COMMENT '字典名称',
  `dict_type` varchar(100) NOT NULL COMMENT '字典类型',
  `status` tinyint(1) NOT NULL COMMENT '是否启用(True:启用 False:禁用)',
  `creator_id` int DEFAULT NULL COMMENT '创建人ID',
  `id` int NOT NULL AUTO_INCREMENT COMMENT '主键ID',
  `description` text COMMENT '备注/描述',
  `created_at` datetime DEFAULT NULL COMMENT '创建时间',
  `updated_at` datetime DEFAULT NULL COMMENT '更新时间',
  PRIMARY KEY (`id`),
  UNIQUE KEY `dict_name` (`dict_name`),
  UNIQUE KEY `dict_type` (`dict_type`),
  KEY `ix_system_dict_type_creator_id` (`creator_id`)
) ENGINE=InnoDB AUTO_INCREMENT=11 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci COMMENT='字典类型表';
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `system_dict_type`
--

/*!40000 ALTER TABLE `system_dict_type` DISABLE KEYS */;
INSERT INTO `system_dict_type` VALUES ('用户性别','sys_user_sex',1,1,1,'用户性别列表','2025-09-28 23:38:17','2025-09-28 23:38:17'),('系统是否','sys_yes_no',1,1,2,'系统是否列表','2025-09-28 23:38:17','2025-09-28 23:38:17'),('系统状态','sys_common_status',1,1,3,'系统状态','2025-09-28 23:38:17','2025-09-28 23:38:17'),('通知类型','sys_notice_type',1,1,4,'通知类型列表','2025-09-28 23:38:17','2025-09-28 23:38:17'),('操作类型','sys_oper_type',1,1,5,'操作类型列表','2025-09-28 23:38:17','2025-09-28 23:38:17'),('任务存储器','sys_job_store',1,1,6,'任务分组列表','2025-09-28 23:38:17','2025-09-28 23:38:17'),('任务执行器','sys_job_executor',1,1,7,'任务执行器列表','2025-09-28 23:38:17','2025-09-28 23:38:17'),('任务函数','sys_job_function',1,1,8,'任务函数列表','2025-09-28 23:38:17','2025-09-28 23:38:17'),('任务触发器','sys_job_trigger',1,1,9,'任务触发器列表','2025-09-28 23:38:17','2025-09-28 23:38:17'),('表格回显样式','sys_list_class',1,1,10,'表格回显样式列表','2025-09-28 23:38:17','2025-09-28 23:38:17');
/*!40000 ALTER TABLE `system_dict_type` ENABLE KEYS */;

--
-- Table structure for table `system_log`
--

DROP TABLE IF EXISTS `system_log`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `system_log` (
  `type` int NOT NULL COMMENT '日志类型(1登录日志 2操作日志)',
  `request_path` varchar(255) NOT NULL COMMENT '请求路径',
  `request_method` varchar(10) NOT NULL COMMENT '请求方式',
  `request_payload` text COMMENT '请求体',
  `request_ip` varchar(50) DEFAULT NULL COMMENT '请求IP地址',
  `login_location` varchar(255) DEFAULT NULL COMMENT '登录位置',
  `request_os` varchar(64) DEFAULT NULL COMMENT '操作系统',
  `request_browser` varchar(64) DEFAULT NULL COMMENT '浏览器',
  `response_code` int NOT NULL COMMENT '响应状态码',
  `response_json` text COMMENT '响应体',
  `process_time` varchar(20) DEFAULT NULL COMMENT '处理时间',
  `creator_id` int DEFAULT NULL COMMENT '创建人ID',
  `id` int NOT NULL AUTO_INCREMENT COMMENT '主键ID',
  `description` text COMMENT '备注/描述',
  `created_at` datetime DEFAULT NULL COMMENT '创建时间',
  `updated_at` datetime DEFAULT NULL COMMENT '更新时间',
  PRIMARY KEY (`id`),
  KEY `ix_system_log_creator_id` (`creator_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci COMMENT='系统日志表';
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `system_log`
--

/*!40000 ALTER TABLE `system_log` DISABLE KEYS */;
/*!40000 ALTER TABLE `system_log` ENABLE KEYS */;

--
-- Table structure for table `system_menu`
--

DROP TABLE IF EXISTS `system_menu`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `system_menu` (
  `id` int NOT NULL AUTO_INCREMENT COMMENT '主键ID',
  `name` varchar(50) NOT NULL COMMENT '菜单名称',
  `type` int NOT NULL COMMENT '菜单类型(1:目录 2:菜单 3:按钮/权限 4:链接)',
  `order` int NOT NULL COMMENT '显示排序',
  `status` tinyint(1) NOT NULL COMMENT '是否启用(True:启用 False:禁用)',
  `permission` varchar(100) DEFAULT NULL COMMENT '权限标识(如：system:user:list)',
  `icon` varchar(50) DEFAULT NULL COMMENT '菜单图标',
  `route_name` varchar(100) DEFAULT NULL COMMENT '路由名称',
  `route_path` varchar(200) DEFAULT NULL COMMENT '路由路径',
  `component_path` varchar(200) DEFAULT NULL COMMENT '组件路径',
  `redirect` varchar(200) DEFAULT NULL COMMENT '重定向地址',
  `hidden` tinyint(1) NOT NULL COMMENT '是否隐藏(True:隐藏 False:显示)',
  `keep_alive` tinyint(1) NOT NULL COMMENT '是否缓存(True:是 False:否)',
  `always_show` tinyint(1) NOT NULL COMMENT '是否始终显示(True:是 False:否)',
  `title` varchar(50) DEFAULT NULL COMMENT '菜单标题',
  `params` json DEFAULT NULL COMMENT '路由参数(JSON对象)',
  `affix` tinyint(1) NOT NULL COMMENT '是否固定标签页(True:是 False:否)',
  `parent_id` int DEFAULT NULL COMMENT '父菜单ID',
  `description` text COMMENT '备注/描述',
  `created_at` datetime DEFAULT NULL COMMENT '创建时间',
  `updated_at` datetime DEFAULT NULL COMMENT '更新时间',
  PRIMARY KEY (`id`),
  UNIQUE KEY `name` (`name`),
  KEY `ix_system_menu_parent_id` (`parent_id`),
  CONSTRAINT `system_menu_ibfk_1` FOREIGN KEY (`parent_id`) REFERENCES `system_menu` (`id`) ON DELETE SET NULL
) ENGINE=InnoDB AUTO_INCREMENT=117 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci COMMENT='菜单表';
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `system_menu`
--

/*!40000 ALTER TABLE `system_menu` DISABLE KEYS */;
INSERT INTO `system_menu` VALUES (1,'仪表盘',1,1,1,'','client','Dashboard','/dashboard',NULL,'/dashboard/workplace',0,1,1,'仪表盘','null',0,NULL,'初始化数据','2025-09-28 23:38:17','2025-09-28 23:38:17'),(2,'系统管理',1,2,1,NULL,'system','System','/system',NULL,'/system/menu',0,1,0,'系统管理','null',0,NULL,'初始化数据','2025-09-28 23:38:17','2025-09-28 23:38:17'),(3,'监控管理',1,3,1,NULL,'monitor','Monitor','/monitor',NULL,'/monitor/online',0,0,0,'监控管理','null',0,NULL,'初始化数据','2025-09-28 23:38:17','2025-09-28 23:38:17'),(4,'公共模块',1,4,1,NULL,'document','Common','/common',NULL,'/common/docs',0,0,0,'公共模块','null',0,NULL,'初始化数据','2025-09-28 23:38:17','2025-09-28 23:38:17'),(5,'演示模块',1,5,1,NULL,'el-icon-Document','Demo','/demo',NULL,'/demo/example',0,0,0,'演示模块','null',0,NULL,'初始化数据','2025-09-28 23:38:17','2025-09-28 23:38:17'),(6,'应用管理',1,6,1,NULL,'el-icon-ShoppingBag','Application','/application',NULL,'/application/myapp',0,0,0,'应用管理','null',0,NULL,'初始化数据','2025-09-28 23:38:17','2025-09-28 23:38:17'),(7,'AI大模型',1,8,1,NULL,'el-icon-Pointer','AI','/ai',NULL,'/ai/mcp',0,0,0,'AI大模型','null',0,NULL,'AI大模型管理','2025-09-28 23:38:17','2025-09-28 23:38:17'),(8,'代码管理',1,9,1,NULL,'code','Gencode','/gencode',NULL,'/ai/mcp',0,0,0,'代码管理','null',0,NULL,'代码管理','2025-09-28 23:38:17','2025-09-28 23:38:17'),(9,'流程管理',1,10,1,NULL,'el-icon-ShoppingBag','Workflow','/workflow',NULL,'/workflow/operator',0,0,0,'流程管理','null',0,NULL,'流程管理','2025-09-28 23:38:17','2025-09-28 23:38:17'),(10,'工作台',2,1,1,'dashboard:workplace:query','homepage','Workplace','/dashboard/workplace','dashboard/workplace',NULL,0,1,0,'工作台','null',1,1,'初始化数据','2025-09-28 23:38:17','2025-09-28 23:38:17'),(11,'分析页',2,2,1,'dashboard:analysis:query','el-icon-PieChart','Analysis','/dashboard/analysis','dashboard/analysis',NULL,0,1,0,'分析页','null',0,1,'初始化数据','2025-09-28 23:38:17','2025-09-28 23:38:17'),(12,'菜单管理',2,1,1,'system:menu:query','menu','Menu','/system/menu','system/menu/index',NULL,0,1,0,'菜单管理','null',0,2,'初始化数据','2025-09-28 23:38:17','2025-09-28 23:38:17'),(13,'部门管理',2,2,1,'system:dept:query','tree','Dept','/system/dept','system/dept/index',NULL,0,1,0,'部门管理','null',0,2,'初始化数据','2025-09-28 23:38:17','2025-09-28 23:38:17'),(14,'岗位管理',2,3,1,'system:position:query','el-icon-Coordinate','Position','/system/position','system/position/index',NULL,0,1,0,'岗位管理','null',0,2,'初始化数据','2025-09-28 23:38:17','2025-09-28 23:38:17'),(15,'角色管理',2,4,1,'system:role:query','role','Role','/system/role','system/role/index',NULL,0,1,0,'角色管理','null',0,2,'初始化数据','2025-09-28 23:38:17','2025-09-28 23:38:17'),(16,'用户管理',2,5,1,'system:user:query','el-icon-User','User','/system/user','system/user/index',NULL,0,1,0,'用户管理','null',0,2,'初始化数据','2025-09-28 23:38:17','2025-09-28 23:38:17'),(17,'日志管理',2,6,1,'system:log:query','el-icon-Aim','Log','/system/log','system/log/index',NULL,0,1,0,'日志管理','null',0,2,'初始化数据','2025-09-28 23:38:17','2025-09-28 23:38:17'),(18,'公告管理',2,7,1,'system:notice:query','bell','Notice','/system/notice','system/notice/index',NULL,0,1,0,'公告管理','null',0,2,'初始化数据','2025-09-28 23:38:17','2025-09-28 23:38:17'),(19,'参数管理',2,8,1,'system:param:query','setting','Config','/system/config','system/config/index',NULL,0,1,0,'参数管理','null',0,2,'初始化数据','2025-09-28 23:38:17','2025-09-28 23:38:17'),(20,'字典管理',2,9,1,'system:dict_type:query','dict','Dict','/system/dict','system/dict/index',NULL,0,1,0,'字典管理','null',0,2,'初始化数据','2025-09-28 23:38:17','2025-09-28 23:38:17'),(21,'任务管理',2,1,1,'monitor:job:query','el-icon-DataLine','Job','/monitor/job','monitor/job/index',NULL,0,1,0,'任务管理','null',0,3,'初始化数据','2025-09-28 23:38:17','2025-09-28 23:38:17'),(22,'在线用户',2,2,1,'monitor:online:query','el-icon-Headset','MonitorOnline','/monitor/online','monitor/online/index',NULL,0,0,0,'在线用户','null',0,3,'初始化数据','2025-09-28 23:38:17','2025-09-28 23:38:17'),(23,'服务器监控',2,3,1,'monitor:server:query','el-icon-Odometer','MonitorServer','/monitor/server','monitor/server/index',NULL,0,0,0,'服务器监控','null',0,3,'初始化数据','2025-09-28 23:38:17','2025-09-28 23:38:17'),(24,'缓存监控',2,4,1,'monitor:cache:query','el-icon-Stopwatch','MonitorCache','/monitor/cache','monitor/cache/index',NULL,0,0,0,'缓存监控','null',0,3,'初始化数据','2025-09-28 23:38:17','2025-09-28 23:38:17'),(25,'文件管理',2,1,1,'monitor:resource:query','el-icon-Files','Resource','/monitor/resource','monitor/resource/index',NULL,0,1,0,'文件管理','null',0,3,'初始化数据','2025-09-28 23:38:17','2025-09-28 23:38:17'),(26,'接口管理',4,1,1,'common:docs:query','api','Docs','/common/docs','common/docs/index',NULL,0,0,0,'接口管理','null',0,4,'初始化数据','2025-09-28 23:38:17','2025-09-28 23:38:17'),(27,'文档管理',4,2,1,'common:redoc:query','el-icon-Document','Redoc','/common/redoc','common/redoc/index',NULL,0,0,0,'文档管理','null',0,4,'初始化数据','2025-09-28 23:38:17','2025-09-28 23:38:17'),(28,'示例管理',2,1,1,'demo:example:query','el-icon-DataLine','Example','/demo/example','demo/example/index',NULL,0,1,0,'示例管理','null',0,5,'初始化数据','2025-09-28 23:38:17','2025-09-28 23:38:17'),(29,'我的应用',2,1,1,'application:myapp:query','el-icon-ShoppingCartFull','ApplicationSystem','/application/myapp','application/myapp/index',NULL,0,1,0,'我的应用','null',0,6,'初始化数据','2025-09-28 23:38:17','2025-09-28 23:38:17'),(30,'MCP应用',2,1,1,'ai:mcp:chat','el-icon-ToiletPaper','MCP','/ai/mcp','ai/mcp/index',NULL,0,1,0,'MCP应用','null',0,7,'MCP智能助手','2025-09-28 23:38:17','2025-09-28 23:38:17'),(31,'代码生成',2,1,1,'generator:gencode:query','code','Backcode','/gencode/backcode','gencode/backcode/index',NULL,0,1,0,'代码生成','null',0,8,'代码生成','2025-09-28 23:38:17','2025-09-28 23:38:17'),(32,'前端构建',2,2,1,'gencode:webcode:query','el-icon-Wallet','webcode','/gencode/webcode','gencode/webcode/index',NULL,0,1,0,'前端构建','null',0,8,'前端构建','2025-09-28 23:38:17','2025-09-28 23:38:17'),(33,'我的流程',2,1,1,'workflow:operator:query','el-icon-ShoppingBag','Operator','/workflow/operator','workflow/operator/index',NULL,0,1,0,'我的流程','null',0,9,'我的流程','2025-09-28 23:38:17','2025-09-28 23:38:17'),(34,'创建菜单',3,1,1,'system:menu:create',NULL,NULL,NULL,NULL,NULL,0,1,0,'创建菜单','null',0,12,'初始化数据','2025-09-28 23:38:17','2025-09-28 23:38:17'),(35,'修改菜单',3,2,1,'system:menu:update',NULL,NULL,NULL,NULL,NULL,0,1,0,'修改菜单','null',0,12,'初始化数据','2025-09-28 23:38:17','2025-09-28 23:38:17'),(36,'删除菜单',3,3,1,'system:menu:delete',NULL,NULL,NULL,NULL,NULL,0,1,0,'删除菜单','null',0,12,'初始化数据','2025-09-28 23:38:17','2025-09-28 23:38:17'),(37,'批量修改菜单状态',3,4,1,'system:menu:patch',NULL,NULL,NULL,NULL,NULL,0,1,0,'批量修改菜单状态','null',0,12,'初始化数据','2025-09-28 23:38:17','2025-09-28 23:38:17'),(38,'创建部门',3,1,1,'system:dept:create',NULL,NULL,NULL,NULL,NULL,0,1,0,'创建部门','null',0,13,'初始化数据','2025-09-28 23:38:17','2025-09-28 23:38:17'),(39,'修改部门',3,2,1,'system:dept:update',NULL,NULL,NULL,NULL,NULL,0,1,0,'修改部门','null',0,13,'初始化数据','2025-09-28 23:38:17','2025-09-28 23:38:17'),(40,'删除部门',3,3,1,'system:dept:delete',NULL,NULL,NULL,NULL,NULL,0,1,0,'删除部门','null',0,13,'初始化数据','2025-09-28 23:38:17','2025-09-28 23:38:17'),(41,'批量修改部门状态',3,4,1,'system:dept:patch',NULL,NULL,NULL,NULL,NULL,0,1,0,'批量修改部门状态','null',0,13,'初始化数据','2025-09-28 23:38:17','2025-09-28 23:38:17'),(42,'创建岗位',3,1,1,'system:position:create',NULL,NULL,NULL,NULL,NULL,0,1,0,'创建岗位','null',0,14,'初始化数据','2025-09-28 23:38:17','2025-09-28 23:38:17'),(43,'修改岗位',3,2,1,'system:position:update',NULL,NULL,NULL,NULL,NULL,0,1,0,'修改岗位','null',0,14,'初始化数据','2025-09-28 23:38:17','2025-09-28 23:38:17'),(44,'删除岗位',3,3,1,'system:position:delete',NULL,NULL,NULL,NULL,NULL,0,1,0,'修改岗位','null',0,14,'初始化数据','2025-09-28 23:38:17','2025-09-28 23:38:17'),(45,'批量修改岗位状态',3,4,1,'system:position:patch',NULL,NULL,NULL,NULL,NULL,0,1,0,'批量修改岗位状态','null',0,14,'初始化数据','2025-09-28 23:38:17','2025-09-28 23:38:17'),(46,'岗位导出',3,5,1,'system:position:export',NULL,NULL,NULL,NULL,NULL,0,1,0,'岗位导出','null',0,14,'初始化数据','2025-09-28 23:38:17','2025-09-28 23:38:17'),(47,'设置角色权限',3,8,1,'system:role:permission',NULL,NULL,NULL,NULL,NULL,0,1,0,'设置角色权限','null',0,14,'初始化数据','2025-09-28 23:38:17','2025-09-28 23:38:17'),(48,'创建角色',3,1,1,'system:role:create',NULL,NULL,NULL,NULL,NULL,0,1,0,'创建角色','null',0,15,'初始化数据','2025-09-28 23:38:17','2025-09-28 23:38:17'),(49,'修改角色',3,2,1,'system:role:update',NULL,NULL,NULL,NULL,NULL,0,1,0,'修改角色','null',0,15,'初始化数据','2025-09-28 23:38:17','2025-09-28 23:38:17'),(50,'删除角色',3,3,1,'system:role:delete',NULL,NULL,NULL,NULL,NULL,0,1,0,'删除角色','null',0,15,'初始化数据','2025-09-28 23:38:17','2025-09-28 23:38:17'),(51,'批量修改角色状态',3,4,1,'system:role:patch',NULL,NULL,NULL,NULL,NULL,0,1,0,'批量修改角色状态','null',0,15,'初始化数据','2025-09-28 23:38:17','2025-09-28 23:38:17'),(52,'角色导出',3,6,1,'system:role:export',NULL,NULL,NULL,NULL,NULL,0,1,0,'角色导出','null',0,15,'初始化数据','2025-09-28 23:38:17','2025-09-28 23:38:17'),(53,'创建用户',3,1,1,'system:user:create',NULL,NULL,NULL,NULL,NULL,0,1,0,'创建用户','null',0,16,'初始化数据','2025-09-28 23:38:17','2025-09-28 23:38:17'),(54,'修改用户',3,2,1,'system:user:update',NULL,NULL,NULL,NULL,NULL,0,1,0,'修改用户','null',0,16,'初始化数据','2025-09-28 23:38:17','2025-09-28 23:38:17'),(55,'删除用户',3,3,1,'system:user:delete',NULL,NULL,NULL,NULL,NULL,0,1,0,'删除用户','null',0,16,'初始化数据','2025-09-28 23:38:17','2025-09-28 23:38:17'),(56,'批量修改用户状态',3,4,1,'system:user:patch',NULL,NULL,NULL,NULL,NULL,0,1,0,'批量修改用户状态','null',0,16,'初始化数据','2025-09-28 23:38:17','2025-09-28 23:38:17'),(57,'导出用户',3,5,1,'system:user:export',NULL,NULL,NULL,NULL,NULL,0,1,0,'导出用户','null',0,16,'初始化数据','2025-09-28 23:38:17','2025-09-28 23:38:17'),(58,'导入用户',3,6,1,'system:user:import',NULL,NULL,NULL,NULL,NULL,0,1,0,'导入用户','null',0,16,'初始化数据','2025-09-28 23:38:17','2025-09-28 23:38:17'),(59,'日志删除',3,1,1,'system:operation_log:delete',NULL,NULL,NULL,NULL,NULL,0,1,0,'日志删除','null',0,17,'初始化数据','2025-09-28 23:38:17','2025-09-28 23:38:17'),(60,'日志导出',3,2,1,'system:operation_log:export',NULL,NULL,NULL,NULL,NULL,0,1,0,'日志导出','null',0,17,'初始化数据','2025-09-28 23:38:17','2025-09-28 23:38:17'),(61,'公告创建',3,1,1,'system:notice:create',NULL,NULL,NULL,NULL,NULL,0,1,0,'公告创建','null',0,18,'初始化数据','2025-09-28 23:38:17','2025-09-28 23:38:17'),(62,'公告修改',3,2,1,'system:notice:update',NULL,NULL,NULL,NULL,NULL,0,1,0,'修改用户','null',0,18,'初始化数据','2025-09-28 23:38:17','2025-09-28 23:38:17'),(63,'公告删除',3,3,1,'system:notice:delete',NULL,NULL,NULL,NULL,NULL,0,1,0,'公告删除','null',0,18,'初始化数据','2025-09-28 23:38:17','2025-09-28 23:38:17'),(64,'公告导出',3,4,1,'system:notice:export',NULL,NULL,NULL,NULL,NULL,0,1,0,'公告导出','null',0,18,'初始化数据','2025-09-28 23:38:17','2025-09-28 23:38:17'),(65,'公告批量修改状态',3,5,1,'system:notice:patch',NULL,NULL,NULL,NULL,NULL,0,1,0,'公告批量修改状态','null',0,18,'初始化数据','2025-09-28 23:38:17','2025-09-28 23:38:17'),(66,'创建参数',3,1,1,'system:param:create',NULL,NULL,NULL,NULL,NULL,0,1,0,'创建参数','null',0,19,'初始化数据','2025-09-28 23:38:17','2025-09-28 23:38:17'),(67,'修改参数',3,2,1,'system:param:update',NULL,NULL,NULL,NULL,NULL,0,1,0,'修改参数','null',0,19,'初始化数据','2025-09-28 23:38:17','2025-09-28 23:38:17'),(68,'删除参数',3,3,1,'system:param:delete',NULL,NULL,NULL,NULL,NULL,0,1,0,'删除参数','null',0,19,'初始化数据','2025-09-28 23:38:17','2025-09-28 23:38:17'),(69,'导出参数',3,4,1,'system:param:export',NULL,NULL,NULL,NULL,NULL,0,1,0,'导出参数','null',0,19,'初始化数据','2025-09-28 23:38:17','2025-09-28 23:38:17'),(70,'参数上传',3,5,1,'system:param:upload',NULL,NULL,NULL,NULL,NULL,0,1,0,'参数上传','null',0,19,'初始化数据','2025-09-28 23:38:17','2025-09-28 23:38:17'),(71,'创建字典类型',3,1,1,'system:dict_type:create',NULL,NULL,NULL,NULL,NULL,0,1,0,'创建字典类型','null',0,20,'初始化数据','2025-09-28 23:38:17','2025-09-28 23:38:17'),(72,'修改字典类型',3,2,1,'system:dict_type:update',NULL,NULL,NULL,NULL,NULL,0,1,0,'修改字典类型','null',0,20,'初始化数据','2025-09-28 23:38:17','2025-09-28 23:38:17'),(73,'删除字典类型',3,3,1,'system:dict_type:delete',NULL,NULL,NULL,NULL,NULL,0,1,0,'删除字典类型','null',0,20,'初始化数据','2025-09-28 23:38:17','2025-09-28 23:38:17'),(74,'导出字典类型',3,4,1,'system:dict_type:export',NULL,NULL,NULL,NULL,NULL,0,1,0,'导出字典类型','null',0,20,'初始化数据','2025-09-28 23:38:17','2025-09-28 23:38:17'),(75,'批量修改字典状态',3,5,1,'system:dict_type:patch',NULL,NULL,NULL,NULL,NULL,0,1,0,'导出字典类型','null',0,20,'初始化数据','2025-09-28 23:38:17','2025-09-28 23:38:17'),(76,'字典数据查询',3,6,1,'system:dict_data:query',NULL,NULL,NULL,NULL,NULL,0,1,0,'字典数据查询','null',0,20,'初始化数据','2025-09-28 23:38:17','2025-09-28 23:38:17'),(77,'创建字典数据',3,7,1,'system:dict_data:create',NULL,NULL,NULL,NULL,NULL,0,1,0,'创建字典数据','null',0,20,'初始化数据','2025-09-28 23:38:17','2025-09-28 23:38:17'),(78,'修改字典数据',3,8,1,'system:dict_data:update',NULL,NULL,NULL,NULL,NULL,0,1,0,'修改字典数据','null',0,20,'初始化数据','2025-09-28 23:38:17','2025-09-28 23:38:17'),(79,'删除字典数据',3,9,1,'system:dict_data:delete',NULL,NULL,NULL,NULL,NULL,0,1,0,'删除字典数据','null',0,20,'初始化数据','2025-09-28 23:38:17','2025-09-28 23:38:17'),(80,'导出字典数据',3,10,1,'system:dict_data:export',NULL,NULL,NULL,NULL,NULL,0,1,0,'导出字典数据','null',0,20,'初始化数据','2025-09-28 23:38:17','2025-09-28 23:38:17'),(81,'批量修改字典数据状态',3,11,1,'system:dict_data:patch',NULL,NULL,NULL,NULL,NULL,0,1,0,'批量修改字典数据状态','null',0,20,'初始化数据','2025-09-28 23:38:17','2025-09-28 23:38:17'),(82,'创建任务',3,1,1,'monitor:job:create',NULL,NULL,NULL,NULL,NULL,0,1,0,'创建任务','null',0,21,'初始化数据','2025-09-28 23:38:17','2025-09-28 23:38:17'),(83,'修改和操作任务',3,2,1,'monitor:job:update',NULL,NULL,NULL,NULL,NULL,0,1,0,'修改和操作任务','null',0,21,'初始化数据','2025-09-28 23:38:17','2025-09-28 23:38:17'),(84,'删除和清除任务',3,3,1,'monitor:job:delete',NULL,NULL,NULL,NULL,NULL,0,1,0,'删除和清除任务','null',0,21,'初始化数据','2025-09-28 23:38:17','2025-09-28 23:38:17'),(85,'导出定时任务',3,4,1,'monitor:job:export',NULL,NULL,NULL,NULL,NULL,0,1,0,'导出定时任务','null',0,21,'初始化数据','2025-09-28 23:38:17','2025-09-28 23:38:17'),(86,'在线用户强制下线',3,1,1,'monitor:online:delete',NULL,NULL,NULL,NULL,NULL,0,0,0,'在线用户强制下线','null',0,22,'初始化数据','2025-09-28 23:38:17','2025-09-28 23:38:17'),(87,'清除缓存',3,1,1,'monitor:cache:delete',NULL,NULL,NULL,NULL,NULL,0,0,0,'清除缓存','null',0,24,'初始化数据','2025-09-28 23:38:17','2025-09-28 23:38:17'),(88,'文件上传',3,1,1,'monitor:resource:upload',NULL,NULL,NULL,NULL,NULL,0,1,0,'文件上传','null',0,25,'初始化数据','2025-09-28 23:38:17','2025-09-28 23:38:17'),(89,'文件下载',3,2,1,'monitor:resource:download',NULL,NULL,NULL,NULL,NULL,0,1,0,'文件下载','null',0,25,'初始化数据','2025-09-28 23:38:17','2025-09-28 23:38:17'),(90,'文件删除',3,3,1,'monitor:resource:delete',NULL,NULL,NULL,NULL,NULL,0,1,0,'文件删除','null',0,25,'初始化数据','2025-09-28 23:38:17','2025-09-28 23:38:17'),(91,'文件移动',3,4,1,'monitor:resource:move',NULL,NULL,NULL,NULL,NULL,0,1,0,'文件移动','null',0,25,'初始化数据','2025-09-28 23:38:17','2025-09-28 23:38:17'),(92,'文件复制',3,5,1,'rmonitor:resource:copy',NULL,NULL,NULL,NULL,NULL,0,1,0,'文件复制','null',0,25,'初始化数据','2025-09-28 23:38:17','2025-09-28 23:38:17'),(93,'文件重命名',3,6,1,'monitor:resource:rename',NULL,NULL,NULL,NULL,NULL,0,1,0,'文件重命名','null',0,25,'初始化数据','2025-09-28 23:38:17','2025-09-28 23:38:17'),(94,'创建目录',3,7,1,'monitor:resource:create_dir',NULL,NULL,NULL,NULL,NULL,0,1,0,'创建目录','null',0,25,'初始化数据','2025-09-28 23:38:17','2025-09-28 23:38:17'),(95,'导出文件列表',3,9,1,'rmonitor:resource:export',NULL,NULL,NULL,NULL,NULL,0,1,0,'导出文件列表','null',0,25,'初始化数据','2025-09-28 23:38:17','2025-09-28 23:38:17'),(96,'创建示例',3,1,1,'demo:example:create',NULL,NULL,NULL,NULL,NULL,0,1,0,'创建示例','null',0,28,'初始化数据','2025-09-28 23:38:17','2025-09-28 23:38:17'),(97,'更新示例',3,2,1,'demo:example:update',NULL,NULL,NULL,NULL,NULL,0,1,0,'更新示例','null',0,28,'初始化数据','2025-09-28 23:38:17','2025-09-28 23:38:17'),(98,'删除示例',3,3,1,'demo:example:delete',NULL,NULL,NULL,NULL,NULL,0,1,0,'删除示例','null',0,28,'初始化数据','2025-09-28 23:38:17','2025-09-28 23:38:17'),(99,'批量修改示例状态',3,4,1,'demo:example:patch',NULL,NULL,NULL,NULL,NULL,0,1,0,'批量修改示例状态','null',0,28,'初始化数据','2025-09-28 23:38:17','2025-09-28 23:38:17'),(100,'导出示例',3,5,1,'demo:example:export',NULL,NULL,NULL,NULL,NULL,0,1,0,'导出示例','null',0,28,'初始化数据','2025-09-28 23:38:17','2025-09-28 23:38:17'),(101,'导入示例',3,6,1,'demo:example:import',NULL,NULL,NULL,NULL,NULL,0,1,0,'导入示例','null',0,28,'初始化数据','2025-09-28 23:38:17','2025-09-28 23:38:17'),(102,'下载导入示例模版',3,7,1,'demo:example:download',NULL,NULL,NULL,NULL,NULL,0,1,0,'下载导入示例模版','null',0,28,'初始化数据','2025-09-28 23:38:17','2025-09-28 23:38:17'),(103,'创建应用',3,1,1,'application:myapp:create',NULL,NULL,NULL,NULL,NULL,0,1,0,'创建应用','null',0,29,'初始化数据','2025-09-28 23:38:17','2025-09-28 23:38:17'),(104,'修改应用',3,2,1,'application:myapp:update',NULL,NULL,NULL,NULL,NULL,0,1,0,'修改应用','null',0,29,'初始化数据','2025-09-28 23:38:17','2025-09-28 23:38:17'),(105,'删除应用',3,3,1,'application:myapp:delete',NULL,NULL,NULL,NULL,NULL,0,1,0,'删除应用','null',0,29,'初始化数据','2025-09-28 23:38:17','2025-09-28 23:38:17'),(106,'批量修改应用状态',3,4,1,'application:myapp:patch',NULL,NULL,NULL,NULL,NULL,0,1,0,'批量修改应用状态','null',0,29,'初始化数据','2025-09-28 23:38:17','2025-09-28 23:38:17'),(107,'智能对话',3,1,1,'ai:mcp:chat',NULL,NULL,NULL,NULL,NULL,0,1,0,'智能对话','null',0,30,'智能对话','2025-09-28 23:38:17','2025-09-28 23:38:17'),(108,'查询代码生成业务表列表',3,1,1,'generator:gencode:query',NULL,NULL,NULL,NULL,NULL,0,1,0,'查询代码生成业务表列表','null',0,31,'查询代码生成业务表列表','2025-09-28 23:38:17','2025-09-28 23:38:17'),(109,'创建表结构',3,2,1,'generator:gencode:create',NULL,NULL,NULL,NULL,NULL,0,1,0,'创建表结构','null',0,31,'创建表结构','2025-09-28 23:38:17','2025-09-28 23:38:17'),(110,'编辑业务表信息',3,3,1,'generator:gencode:update',NULL,NULL,NULL,NULL,NULL,0,1,0,'编辑业务表信息','null',0,31,'编辑业务表信息','2025-09-28 23:38:17','2025-09-28 23:38:17'),(111,'删除业务表信息',3,4,1,'generator:gencode:delete',NULL,NULL,NULL,NULL,NULL,0,1,0,'删除业务表信息','null',0,31,'删除业务表信息','2025-09-28 23:38:17','2025-09-28 23:38:17'),(112,'导入表结构',3,5,1,'generator:gencode:import',NULL,NULL,NULL,NULL,NULL,0,1,0,'导入表结构','null',0,31,'导入表结构','2025-09-28 23:38:17','2025-09-28 23:38:17'),(113,'批量生成代码',3,6,1,'generator:gencode:operate',NULL,NULL,NULL,NULL,NULL,0,1,0,'批量生成代码','null',0,31,'批量生成代码','2025-09-28 23:38:17','2025-09-28 23:38:17'),(114,'生成代码到指定路径',3,7,1,'generator:gencode:code',NULL,NULL,NULL,NULL,NULL,0,1,0,'生成代码到指定路径','null',0,31,'生成代码到指定路径','2025-09-28 23:38:17','2025-09-28 23:38:17'),(115,'查询数据库表列表',3,8,1,'generator:dblist:query',NULL,NULL,NULL,NULL,NULL,0,1,0,'查询数据库表列表','null',0,31,'查询数据库表列表','2025-09-28 23:38:17','2025-09-28 23:38:17'),(116,'同步数据库',3,9,1,'generator:db:sync',NULL,NULL,NULL,NULL,NULL,0,1,0,'同步数据库','null',0,31,'同步数据库','2025-09-28 23:38:17','2025-09-28 23:38:17');
/*!40000 ALTER TABLE `system_menu` ENABLE KEYS */;

--
-- Table structure for table `system_notice`
--

DROP TABLE IF EXISTS `system_notice`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `system_notice` (
  `notice_title` varchar(50) NOT NULL COMMENT '公告标题',
  `notice_type` varchar(50) NOT NULL COMMENT '公告类型（1通知 2公告）',
  `notice_content` text COMMENT '公告内容',
  `status` tinyint(1) NOT NULL COMMENT '是否启用(True:启用 False:禁用)',
  `creator_id` int DEFAULT NULL COMMENT '创建人ID',
  `id` int NOT NULL AUTO_INCREMENT COMMENT '主键ID',
  `description` text COMMENT '备注/描述',
  `created_at` datetime DEFAULT NULL COMMENT '创建时间',
  `updated_at` datetime DEFAULT NULL COMMENT '更新时间',
  PRIMARY KEY (`id`),
  KEY `ix_system_notice_creator_id` (`creator_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci COMMENT='通知公告表';
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `system_notice`
--

/*!40000 ALTER TABLE `system_notice` DISABLE KEYS */;
/*!40000 ALTER TABLE `system_notice` ENABLE KEYS */;

--
-- Table structure for table `system_param`
--

DROP TABLE IF EXISTS `system_param`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `system_param` (
  `config_name` varchar(500) NOT NULL COMMENT '参数名称',
  `config_key` varchar(500) NOT NULL COMMENT '参数键名',
  `config_value` varchar(500) DEFAULT NULL COMMENT '参数键值',
  `config_type` tinyint(1) DEFAULT NULL COMMENT '系统内置(True:是 False:否)',
  `status` tinyint(1) NOT NULL COMMENT '是否启用(True:启用 False:禁用)',
  `creator_id` int DEFAULT NULL COMMENT '创建人ID',
  `id` int NOT NULL AUTO_INCREMENT COMMENT '主键ID',
  `description` text COMMENT '备注/描述',
  `created_at` datetime DEFAULT NULL COMMENT '创建时间',
  `updated_at` datetime DEFAULT NULL COMMENT '更新时间',
  PRIMARY KEY (`id`),
  UNIQUE KEY `config_name` (`config_name`),
  UNIQUE KEY `config_key` (`config_key`),
  KEY `ix_system_param_creator_id` (`creator_id`)
) ENGINE=InnoDB AUTO_INCREMENT=23 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci COMMENT='系统参数表';
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `system_param`
--

/*!40000 ALTER TABLE `system_param` DISABLE KEYS */;
INSERT INTO `system_param` VALUES ('网站名称','sys_web_title','FastAPI Vue3 Admin',1,1,1,1,'网站名称','2025-09-28 23:38:17','2025-09-28 23:38:17'),('网站描述','sys_web_description','FastAPI Vue3 Admin 是完全开源的权限管理系统',1,1,1,2,'网站描述','2025-09-28 23:38:17','2025-09-28 23:38:17'),('网页图标','sys_web_favicon','https://service.fastapiadmin.com/api/v1/static/image/favicon.png',1,1,1,3,'网页图标','2025-09-28 23:38:17','2025-09-28 23:38:17'),('网站Logo','sys_web_logo','https://service.fastapiadmin.com/api/v1/static/image/logo.png',1,1,1,4,'网站Logo','2025-09-28 23:38:17','2025-09-28 23:38:17'),('登录背景','sys_login_background','https://service.fastapiadmin.com/api/v1/static/image/background.svg',1,1,1,5,'登录背景','2025-09-28 23:38:17','2025-09-28 23:38:17'),('版权信息','sys_web_copyright','Copyright © 2025-2026 service.fastapiadmin.com 版权所有',1,1,1,6,'版权信息','2025-09-28 23:38:17','2025-09-28 23:38:17'),('备案信息','sys_keep_record','陕ICP备2025069493号-1',1,1,1,7,'备案信息','2025-09-28 23:38:17','2025-09-28 23:38:17'),('帮助文档','sys_help_doc','https://service.fastapiadmin.com',1,1,1,8,'帮助文档','2025-09-28 23:38:17','2025-09-28 23:38:17'),('隐私政策','sys_web_privacy','https://github.com/1014TaoTao/fastapi_vue3_admin/blob/master/LICENSE',1,1,1,9,'隐私政策','2025-09-28 23:38:17','2025-09-28 23:38:17'),('用户协议','sys_web_clause','https://github.com/1014TaoTao/fastapi_vue3_admin/blob/master/LICENSE',1,1,1,10,'用户协议','2025-09-28 23:38:17','2025-09-28 23:38:17'),('源码代码','sys_git_code','https://github.com/1014TaoTao/fastapi_vue3_admin.git',1,1,1,11,'源码代码','2025-09-28 23:38:17','2025-09-28 23:38:17'),('项目版本','sys_web_version','2.0.0',1,1,1,12,'项目版本','2025-09-28 23:38:17','2025-09-28 23:38:17'),('白名单接口','white_api_list_path','[\"/api/v1/system/auth/login\", \"/api/v1/system/auth/token/refresh\", \"/api/v1/system/auth/captcha/get\", \"/api/v1/system/auth/logout\", \"/api/v1/system/config/info\", \"/api/v1/system/user/current/info\", \"/api/v1/system/notice/available\"]',1,1,1,13,'演示模式白名单路径列表','2025-09-28 23:38:17','2025-09-28 23:38:17'),('黑名单接口','black_api_list_path','[\"/auth/login\"]',1,1,1,14,'演示模式黑名单路径列表','2025-09-28 23:38:17','2025-09-28 23:38:17'),('访问IP白名单','ip_white_list','[\"127.0.0.1\", \"117.10.167.220\", \"223.104.208.30\", \"42.80.102.171\"]',1,1,1,15,'演示模式IP白名单列表','2025-09-28 23:38:17','2025-09-28 23:38:17'),('权限认证白名单接口','token_request_path_exclude','[\"api/v1/auth/login\"]',1,1,1,16,'无需JWT认证的路径白名单','2025-09-28 23:38:17','2025-09-28 23:38:17'),('允许上传文件类型','allowed_extensions','[\".bmp\", \".gif\", \".jpg\", \".jpeg\", \".png\", \".ico\", \".svg\", \".csv\", \".doc\", \".docx\", \".xls\", \".xlsx\", \".ppt\", \".pptx\", \".html\", \".htm\", \".txt\", \".pdf\", \".rar\", \".zip\", \".gz\", \".bz2\", \".mp4\", \".avi\", \".rmvb\"]',1,1,1,17,'允许上传的文件类型列表','2025-09-28 23:38:17','2025-09-28 23:38:17'),('最大文件上传大小','max_file_size','10485760',1,1,1,18,'最大文件上传大小(字节)，默认10MB','2025-09-28 23:38:17','2025-09-28 23:38:17'),('操作日志记录开关','operation_log_record','True',1,1,1,19,'是否记录操作日志','2025-09-28 23:38:17','2025-09-28 23:38:17'),('操作日志记录方法','operation_record_method','[\"POST\", \"PUT\", \"PATCH\", \"DELETE\", \"HEAD\", \"OPTIONS\"]',1,1,1,20,'需要记录操作日志的HTTP方法列表','2025-09-28 23:38:17','2025-09-28 23:38:17'),('忽略操作日志函数','ignore_operation_function','[\"get_captcha_for_login\"]',1,1,1,21,'忽略记录操作日志的函数列表','2025-09-28 23:38:17','2025-09-28 23:38:17'),('演示模式启用','demo_enable','False',1,1,1,22,'是否开启演示模式','2025-09-28 23:38:17','2025-09-28 23:38:17');
/*!40000 ALTER TABLE `system_param` ENABLE KEYS */;

--
-- Table structure for table `system_position`
--

DROP TABLE IF EXISTS `system_position`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `system_position` (
  `name` varchar(40) NOT NULL COMMENT '岗位名称',
  `order` int NOT NULL COMMENT '显示排序',
  `status` tinyint(1) NOT NULL COMMENT '是否启用(True:启用 False:禁用)',
  `creator_id` int DEFAULT NULL COMMENT '创建人ID',
  `id` int NOT NULL AUTO_INCREMENT COMMENT '主键ID',
  `description` text COMMENT '备注/描述',
  `created_at` datetime DEFAULT NULL COMMENT '创建时间',
  `updated_at` datetime DEFAULT NULL COMMENT '更新时间',
  PRIMARY KEY (`id`),
  UNIQUE KEY `name` (`name`),
  KEY `ix_system_position_creator_id` (`creator_id`)
) ENGINE=InnoDB AUTO_INCREMENT=2 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci COMMENT='岗位表';
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `system_position`
--

/*!40000 ALTER TABLE `system_position` DISABLE KEYS */;
INSERT INTO `system_position` VALUES ('董事长岗',1,1,1,1,'董事长岗位','2025-09-28 23:38:17','2025-09-28 23:38:17');
/*!40000 ALTER TABLE `system_position` ENABLE KEYS */;

--
-- Table structure for table `system_role`
--

DROP TABLE IF EXISTS `system_role`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `system_role` (
  `name` varchar(40) NOT NULL COMMENT '角色名称',
  `code` varchar(20) DEFAULT NULL COMMENT '角色编码',
  `order` int NOT NULL COMMENT '显示排序',
  `status` tinyint(1) NOT NULL COMMENT '是否启用(True:启用 False:禁用)',
  `data_scope` int NOT NULL COMMENT '数据权限范围',
  `creator_id` int DEFAULT NULL COMMENT '创建人ID',
  `id` int NOT NULL AUTO_INCREMENT COMMENT '主键ID',
  `description` text COMMENT '备注/描述',
  `created_at` datetime DEFAULT NULL COMMENT '创建时间',
  `updated_at` datetime DEFAULT NULL COMMENT '更新时间',
  PRIMARY KEY (`id`),
  UNIQUE KEY `name` (`name`),
  UNIQUE KEY `code` (`code`),
  KEY `ix_system_role_creator_id` (`creator_id`)
) ENGINE=InnoDB AUTO_INCREMENT=2 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci COMMENT='角色表';
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `system_role`
--

/*!40000 ALTER TABLE `system_role` DISABLE KEYS */;
INSERT INTO `system_role` VALUES ('管理员角色','ADMIN',1,1,4,1,1,'管理员','2025-09-28 23:38:17','2025-09-28 23:38:17');
/*!40000 ALTER TABLE `system_role` ENABLE KEYS */;

--
-- Table structure for table `system_role_depts`
--

DROP TABLE IF EXISTS `system_role_depts`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `system_role_depts` (
  `role_id` int NOT NULL COMMENT '角色ID',
  `dept_id` int NOT NULL COMMENT '部门ID',
  PRIMARY KEY (`role_id`,`dept_id`),
  KEY `dept_id` (`dept_id`),
  CONSTRAINT `system_role_depts_ibfk_1` FOREIGN KEY (`role_id`) REFERENCES `system_role` (`id`) ON DELETE CASCADE ON UPDATE CASCADE,
  CONSTRAINT `system_role_depts_ibfk_2` FOREIGN KEY (`dept_id`) REFERENCES `system_dept` (`id`) ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci COMMENT='角色部门关联表';
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `system_role_depts`
--

/*!40000 ALTER TABLE `system_role_depts` DISABLE KEYS */;
INSERT INTO `system_role_depts` VALUES (1,1);
/*!40000 ALTER TABLE `system_role_depts` ENABLE KEYS */;

--
-- Table structure for table `system_role_menus`
--

DROP TABLE IF EXISTS `system_role_menus`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `system_role_menus` (
  `role_id` int NOT NULL COMMENT '角色ID',
  `menu_id` int NOT NULL COMMENT '菜单ID',
  PRIMARY KEY (`role_id`,`menu_id`),
  KEY `menu_id` (`menu_id`),
  CONSTRAINT `system_role_menus_ibfk_1` FOREIGN KEY (`role_id`) REFERENCES `system_role` (`id`) ON DELETE CASCADE ON UPDATE CASCADE,
  CONSTRAINT `system_role_menus_ibfk_2` FOREIGN KEY (`menu_id`) REFERENCES `system_menu` (`id`) ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci COMMENT='角色菜单关联表';
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `system_role_menus`
--

/*!40000 ALTER TABLE `system_role_menus` DISABLE KEYS */;
INSERT INTO `system_role_menus` VALUES (1,1),(1,2),(1,3),(1,4),(1,5),(1,6),(1,7),(1,8),(1,9),(1,10),(1,11),(1,12),(1,13),(1,14),(1,15),(1,16),(1,17),(1,18),(1,19),(1,20),(1,21),(1,22),(1,23),(1,24),(1,25),(1,26),(1,27),(1,28),(1,29),(1,30),(1,31),(1,32),(1,33),(1,34),(1,35),(1,36),(1,37),(1,38),(1,39),(1,40),(1,41),(1,42),(1,43),(1,44),(1,45),(1,46),(1,47),(1,48),(1,49),(1,50),(1,51),(1,52),(1,53),(1,54),(1,55),(1,56),(1,57),(1,58),(1,59),(1,60),(1,61),(1,62),(1,63),(1,64),(1,65),(1,66),(1,67),(1,68),(1,69),(1,70),(1,71),(1,72),(1,73),(1,74),(1,75),(1,76),(1,77),(1,78),(1,79),(1,80),(1,81),(1,82),(1,83),(1,84),(1,85),(1,86),(1,87),(1,88),(1,89),(1,90),(1,91),(1,92),(1,93),(1,94),(1,95),(1,96),(1,97),(1,98),(1,99),(1,100),(1,101),(1,102),(1,103),(1,104),(1,105),(1,106),(1,107),(1,108),(1,109),(1,110),(1,111),(1,112),(1,113),(1,114),(1,115);
/*!40000 ALTER TABLE `system_role_menus` ENABLE KEYS */;

--
-- Table structure for table `system_user_positions`
--

DROP TABLE IF EXISTS `system_user_positions`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `system_user_positions` (
  `user_id` int NOT NULL COMMENT '用户ID',
  `position_id` int NOT NULL COMMENT '岗位ID',
  PRIMARY KEY (`user_id`,`position_id`),
  KEY `position_id` (`position_id`),
  CONSTRAINT `system_user_positions_ibfk_1` FOREIGN KEY (`user_id`) REFERENCES `system_users` (`id`) ON DELETE CASCADE ON UPDATE CASCADE,
  CONSTRAINT `system_user_positions_ibfk_2` FOREIGN KEY (`position_id`) REFERENCES `system_position` (`id`) ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci COMMENT='用户岗位关联表';
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `system_user_positions`
--

/*!40000 ALTER TABLE `system_user_positions` DISABLE KEYS */;
INSERT INTO `system_user_positions` VALUES (1,1),(2,1);
/*!40000 ALTER TABLE `system_user_positions` ENABLE KEYS */;

--
-- Table structure for table `system_user_roles`
--

DROP TABLE IF EXISTS `system_user_roles`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `system_user_roles` (
  `user_id` int NOT NULL COMMENT '用户ID',
  `role_id` int NOT NULL COMMENT '角色ID',
  PRIMARY KEY (`user_id`,`role_id`),
  KEY `role_id` (`role_id`),
  CONSTRAINT `system_user_roles_ibfk_1` FOREIGN KEY (`user_id`) REFERENCES `system_users` (`id`) ON DELETE CASCADE ON UPDATE CASCADE,
  CONSTRAINT `system_user_roles_ibfk_2` FOREIGN KEY (`role_id`) REFERENCES `system_role` (`id`) ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci COMMENT='用户角色关联表';
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `system_user_roles`
--

/*!40000 ALTER TABLE `system_user_roles` DISABLE KEYS */;
INSERT INTO `system_user_roles` VALUES (1,1),(2,1);
/*!40000 ALTER TABLE `system_user_roles` ENABLE KEYS */;

--
-- Table structure for table `system_users`
--

DROP TABLE IF EXISTS `system_users`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `system_users` (
  `username` varchar(32) NOT NULL COMMENT '用户名/登录账号',
  `password` varchar(255) NOT NULL COMMENT '密码哈希',
  `name` varchar(32) NOT NULL COMMENT '昵称',
  `status` tinyint(1) NOT NULL COMMENT '是否启用(True:启用 False:禁用)',
  `mobile` varchar(20) DEFAULT NULL COMMENT '手机号',
  `email` varchar(64) DEFAULT NULL COMMENT '邮箱',
  `gender` varchar(1) DEFAULT NULL COMMENT '性别(0:男 1:女 2:未知)',
  `avatar` varchar(500) DEFAULT NULL COMMENT '头像URL地址',
  `is_superuser` tinyint(1) NOT NULL COMMENT '是否超管',
  `last_login` datetime DEFAULT NULL COMMENT '最后登录时间',
  `dept_id` int DEFAULT NULL COMMENT '部门ID',
  `creator_id` int DEFAULT NULL COMMENT '创建人ID',
  `id` int NOT NULL AUTO_INCREMENT COMMENT '主键ID',
  `description` text COMMENT '备注/描述',
  `created_at` datetime DEFAULT NULL COMMENT '创建时间',
  `updated_at` datetime DEFAULT NULL COMMENT '更新时间',
  PRIMARY KEY (`id`),
  UNIQUE KEY `username` (`username`),
  UNIQUE KEY `mobile` (`mobile`),
  UNIQUE KEY `email` (`email`),
  KEY `ix_system_users_creator_id` (`creator_id`),
  KEY `ix_system_users_dept_id` (`dept_id`),
  CONSTRAINT `system_users_ibfk_1` FOREIGN KEY (`dept_id`) REFERENCES `system_dept` (`id`) ON DELETE SET NULL ON UPDATE CASCADE
) ENGINE=InnoDB AUTO_INCREMENT=3 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci COMMENT='用户表';
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `system_users`
--

/*!40000 ALTER TABLE `system_users` DISABLE KEYS */;
INSERT INTO `system_users` VALUES ('admin','$2b$12$e2IJgS/cvHgJ0H3G7Xa08OXoXnk6N/NX3IZRtubBDElA0VLZhkNOa','管理员',1,'15382112222','admin@qq.com','0','https://service.fastapiadmin.com/api/v1/static/image/avatar.png',1,NULL,1,NULL,1,'管理员','2025-09-28 23:38:17','2025-09-28 23:38:17'),('demo','$2b$12$e2IJgS/cvHgJ0H3G7Xa08OXoXnk6N/NX3IZRtubBDElA0VLZhkNOa','演示用户',1,'15382112121','demo@qq.com','0','https://service.fastapiadmin.com/api/v1/static/image/avatar.png',0,NULL,1,1,2,'演示用户','2025-09-28 23:38:17','2025-09-28 23:38:17');
/*!40000 ALTER TABLE `system_users` ENABLE KEYS */;

--
-- Dumping routines for database 'fastapiadmin'
--
/*!40103 SET TIME_ZONE=@OLD_TIME_ZONE */;

/*!40101 SET SQL_MODE=@OLD_SQL_MODE */;
/*!40014 SET FOREIGN_KEY_CHECKS=@OLD_FOREIGN_KEY_CHECKS */;
/*!40014 SET UNIQUE_CHECKS=@OLD_UNIQUE_CHECKS */;
/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
/*!40111 SET SQL_NOTES=@OLD_SQL_NOTES */;

-- Dump completed on 2025-09-28 23:38:32
