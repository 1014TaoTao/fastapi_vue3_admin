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
-- Table structure for table `application_myapp`
--

DROP TABLE IF EXISTS `application_myapp`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `application_myapp` (
  `name` varchar(64) NOT NULL COMMENT '应用名称',
  `access_url` varchar(500) NOT NULL COMMENT '访问地址',
  `icon_url` varchar(300) DEFAULT NULL COMMENT '应用图标URL',
  `creator_id` int DEFAULT NULL COMMENT '创建人ID',
  `id` int NOT NULL AUTO_INCREMENT COMMENT '主键ID',
  `status` tinyint(1) NOT NULL COMMENT '是否启用(True:启用 False:禁用)',
  `description` text COMMENT '备注说明',
  `created_at` datetime NOT NULL COMMENT '创建时间',
  `updated_at` datetime NOT NULL COMMENT '更新时间',
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
  `creator_id` int DEFAULT NULL COMMENT '创建人ID',
  `id` int NOT NULL AUTO_INCREMENT COMMENT '主键ID',
  `status` tinyint(1) NOT NULL COMMENT '是否启用(True:启用 False:禁用)',
  `description` text COMMENT '备注说明',
  `created_at` datetime NOT NULL COMMENT '创建时间',
  `updated_at` datetime NOT NULL COMMENT '更新时间',
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
  `creator_id` int DEFAULT NULL COMMENT '创建人ID',
  `id` int NOT NULL AUTO_INCREMENT COMMENT '主键ID',
  `status` tinyint(1) NOT NULL COMMENT '是否启用(True:启用 False:禁用)',
  `description` text COMMENT '备注说明',
  `created_at` datetime NOT NULL COMMENT '创建时间',
  `updated_at` datetime NOT NULL COMMENT '更新时间',
  PRIMARY KEY (`id`),
  KEY `ix_monitor_job_creator_id` (`creator_id`)
) ENGINE=InnoDB AUTO_INCREMENT=4 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci COMMENT='定时任务调度表';
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `monitor_job`
--

/*!40000 ALTER TABLE `monitor_job` DISABLE KEYS */;
INSERT INTO `monitor_job` VALUES ('系统默认（无参）','default','default','cron','0 0 12 * * ?','scheduler_test.job',NULL,NULL,0,1,NULL,NULL,1,1,0,NULL,'2025-09-06 01:12:22','2025-09-06 01:12:22'),('系统默认（有参）','default','default','cron','0 0 12 * * ?','scheduler_test.job','test',NULL,0,1,NULL,NULL,1,2,0,NULL,'2025-09-06 01:12:22','2025-09-06 01:12:22'),('系统默认（多参）','default','default','cron','0 0 12 * * ?','scheduler_test.job','new','{\"test\": 111}',0,1,NULL,NULL,1,3,0,NULL,'2025-09-06 01:12:22','2025-09-06 01:12:22');
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
-- Table structure for table `system_config`
--

DROP TABLE IF EXISTS `system_config`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `system_config` (
  `config_name` varchar(500) NOT NULL COMMENT '参数名称',
  `config_key` varchar(500) NOT NULL COMMENT '参数键名',
  `config_value` varchar(500) DEFAULT NULL COMMENT '参数键值',
  `config_type` tinyint(1) DEFAULT NULL COMMENT '系统内置(True:是 False:否)',
  `creator_id` int DEFAULT NULL COMMENT '创建人ID',
  `id` int NOT NULL AUTO_INCREMENT COMMENT '主键ID',
  `status` tinyint(1) NOT NULL COMMENT '是否启用(True:启用 False:禁用)',
  `description` text COMMENT '备注说明',
  `created_at` datetime NOT NULL COMMENT '创建时间',
  `updated_at` datetime NOT NULL COMMENT '更新时间',
  PRIMARY KEY (`id`),
  UNIQUE KEY `config_name` (`config_name`),
  UNIQUE KEY `config_key` (`config_key`),
  KEY `ix_system_config_creator_id` (`creator_id`)
) ENGINE=InnoDB AUTO_INCREMENT=13 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci COMMENT='系统配置表';
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `system_config`
--

/*!40000 ALTER TABLE `system_config` DISABLE KEYS */;
INSERT INTO `system_config` VALUES ('网站名称','sys_web_title','FastAPI Vue3 Admin',1,1,1,1,'网站名称','2025-09-06 01:12:22','2025-09-06 01:12:22'),('网站描述','sys_web_description','FastAPI Vue3 Admin 是完全开源的权限管理系统',1,1,2,1,'网站描述','2025-09-06 01:12:22','2025-09-06 01:12:22'),('网页图标','sys_web_favicon','https://service.fastapiadmin.com/api/v1/static/image/favicon.png',1,1,3,1,'网页图标','2025-09-06 01:12:22','2025-09-06 01:12:22'),('网站Logo','sys_web_logo','https://service.fastapiadmin.com/api/v1/static/image/logo.png',1,1,4,1,'网站Logo','2025-09-06 01:12:22','2025-09-06 01:12:22'),('登录背景','sys_login_background','https://service.fastapiadmin.com/api/v1/static/image/background.svg',1,1,5,1,'登录背景','2025-09-06 01:12:22','2025-09-06 01:12:22'),('版权信息','sys_web_copyright','Copyright © 2025-2026 service.fastapiadmin.com 版权所有',1,1,6,1,'版权信息','2025-09-06 01:12:22','2025-09-06 01:12:22'),('备案信息','sys_keep_record','陕ICP备2025069493号-1',1,1,7,1,'备案信息','2025-09-06 01:12:22','2025-09-06 01:12:22'),('帮助文档','sys_help_doc','https://service.fastapiadmin.com',1,1,8,1,'帮助文档','2025-09-06 01:12:22','2025-09-06 01:12:22'),('隐私政策','sys_web_privacy','https://github.com/1014TaoTao/fastapi_vue3_admin/blob/master/LICENSE',1,1,9,1,'隐私政策','2025-09-06 01:12:22','2025-09-06 01:12:22'),('用户协议','sys_web_clause','https://github.com/1014TaoTao/fastapi_vue3_admin/blob/master/LICENSE',1,1,10,1,'用户协议','2025-09-06 01:12:22','2025-09-06 01:12:22'),('源码代码','sys_git_code','https://github.com/1014TaoTao/fastapi_vue3_admin.git',1,1,11,1,'源码代码','2025-09-06 01:12:22','2025-09-06 01:12:22'),('项目版本','sys_web_version','2.0.0',1,1,12,1,'项目版本','2025-09-06 01:12:22','2025-09-06 01:12:22');
/*!40000 ALTER TABLE `system_config` ENABLE KEYS */;

--
-- Table structure for table `system_dept`
--

DROP TABLE IF EXISTS `system_dept`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `system_dept` (
  `name` varchar(40) NOT NULL COMMENT '部门名称',
  `order` int NOT NULL COMMENT '显示排序',
  `parent_id` int DEFAULT NULL COMMENT '父级部门ID',
  `id` int NOT NULL AUTO_INCREMENT COMMENT '主键ID',
  `status` tinyint(1) NOT NULL COMMENT '是否启用(True:启用 False:禁用)',
  `description` text COMMENT '备注说明',
  `created_at` datetime NOT NULL COMMENT '创建时间',
  `updated_at` datetime NOT NULL COMMENT '更新时间',
  PRIMARY KEY (`id`),
  UNIQUE KEY `name` (`name`),
  KEY `ix_system_dept_parent_id` (`parent_id`),
  CONSTRAINT `system_dept_ibfk_1` FOREIGN KEY (`parent_id`) REFERENCES `system_dept` (`id`) ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB AUTO_INCREMENT=12 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci COMMENT='部门表';
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `system_dept`
--

/*!40000 ALTER TABLE `system_dept` DISABLE KEYS */;
INSERT INTO `system_dept` VALUES ('集团总公司',1,NULL,1,1,'集团总公司','2025-09-06 01:12:22','2025-09-06 01:12:22'),('西安分公司',1,1,2,1,'西安分公司','2025-09-06 01:12:22','2025-09-06 01:12:22'),('深圳分公司',2,1,3,1,'深圳分公司','2025-09-06 01:12:22','2025-09-06 01:12:22'),('开发组',1,2,4,1,'开发组','2025-09-06 01:12:22','2025-09-06 01:12:22'),('测试组',2,2,5,1,'测试组','2025-09-06 01:12:22','2025-09-06 01:12:22'),('演示组',3,2,6,1,'演示组','2025-09-06 01:12:22','2025-09-06 01:12:22'),('销售部',1,3,7,1,'销售部','2025-09-06 01:12:22','2025-09-06 01:12:22'),('市场部',2,3,8,1,'市场部','2025-09-06 01:12:22','2025-09-06 01:12:22'),('财务部',3,3,9,1,'财务部','2025-09-06 01:12:22','2025-09-06 01:12:22'),('研发部',4,3,10,1,'研发部','2025-09-06 01:12:22','2025-09-06 01:12:22'),('运维部',5,3,11,1,'研发部','2025-09-06 01:12:22','2025-09-06 01:12:22');
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
  `css_class` varchar(100) DEFAULT NULL COMMENT '样式属性（其他样式扩展）',
  `list_class` varchar(100) DEFAULT NULL COMMENT '表格回显样式',
  `is_default` tinyint(1) NOT NULL COMMENT '是否默认（True是 False否）',
  `dict_type_id` int DEFAULT NULL COMMENT '字典类型ID',
  `creator_id` int DEFAULT NULL COMMENT '创建人ID',
  `id` int NOT NULL AUTO_INCREMENT COMMENT '主键ID',
  `status` tinyint(1) NOT NULL COMMENT '是否启用(True:启用 False:禁用)',
  `description` text COMMENT '备注说明',
  `created_at` datetime NOT NULL COMMENT '创建时间',
  `updated_at` datetime NOT NULL COMMENT '更新时间',
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
INSERT INTO `system_dict_data` VALUES (1,'男','0','sys_user_sex','blue',NULL,1,NULL,1,1,1,'性别男','2025-09-06 01:12:22','2025-09-06 01:12:22'),(2,'女','1','sys_user_sex','pink',NULL,0,NULL,1,2,1,'性别女','2025-09-06 01:12:22','2025-09-06 01:12:22'),(3,'未知','2','sys_user_sex','red',NULL,0,NULL,1,3,1,'性别未知','2025-09-06 01:12:22','2025-09-06 01:12:22'),(1,'启用','1','sys_common_status','','primary',0,NULL,1,4,1,'启用状态','2025-09-06 01:12:22','2025-09-06 01:12:22'),(2,'停用','0','sys_common_status','','danger',0,NULL,1,5,1,'停用状态','2025-09-06 01:12:22','2025-09-06 01:12:22'),(1,'是','1','sys_yes_no','','primary',1,NULL,1,6,1,'是','2025-09-06 01:12:22','2025-09-06 01:12:22'),(2,'否','0','sys_yes_no','','danger',0,NULL,1,7,1,'否','2025-09-06 01:12:22','2025-09-06 01:12:22'),(99,'其他','0','sys_oper_type','','info',0,NULL,1,8,1,'其他操作','2025-09-06 01:12:22','2025-09-06 01:12:22'),(1,'新增','1','sys_oper_type','','info',0,NULL,1,9,1,'新增操作','2025-09-06 01:12:22','2025-09-06 01:12:22'),(2,'修改','2','sys_oper_type','','info',0,NULL,1,10,1,'修改操作','2025-09-06 01:12:22','2025-09-06 01:12:22'),(3,'删除','3','sys_oper_type','','danger',0,NULL,1,11,1,'删除操作','2025-09-06 01:12:22','2025-09-06 01:12:22'),(4,'分配权限','4','sys_oper_type','','primary',0,NULL,1,12,1,'授权操作','2025-09-06 01:12:22','2025-09-06 01:12:22'),(5,'导出','5','sys_oper_type','','warning',0,NULL,1,13,1,'导出操作','2025-09-06 01:12:22','2025-09-06 01:12:22'),(6,'导入','6','sys_oper_type','','warning',0,NULL,1,14,1,'导入操作','2025-09-06 01:12:22','2025-09-06 01:12:22'),(7,'强退','7','sys_oper_type','','danger',0,NULL,1,15,1,'强退操作','2025-09-06 01:12:22','2025-09-06 01:12:22'),(8,'生成代码','8','sys_oper_type','','warning',0,NULL,1,16,1,'生成操作','2025-09-06 01:12:22','2025-09-06 01:12:22'),(9,'清空数据','9','sys_oper_type','','danger',0,NULL,1,17,1,'清空操作','2025-09-06 01:12:22','2025-09-06 01:12:22'),(1,'通知','1','sys_notice_type','blue','warning',1,NULL,1,18,1,'通知','2025-09-06 01:12:22','2025-09-06 01:12:22'),(2,'公告','2','sys_notice_type','orange','success',0,NULL,1,19,1,'公告','2025-09-06 01:12:22','2025-09-06 01:12:22'),(1,'默认(Memory)','default','sys_job_store','',NULL,1,NULL,1,20,1,'默认分组','2025-09-06 01:12:22','2025-09-06 01:12:22'),(2,'数据库(Sqlalchemy)','sqlalchemy','sys_job_store','',NULL,0,NULL,1,21,1,'数据库分组','2025-09-06 01:12:22','2025-09-06 01:12:22'),(3,'数据库(Redis)','redis','sys_job_store','',NULL,0,NULL,1,22,1,'reids分组','2025-09-06 01:12:22','2025-09-06 01:12:22'),(1,'线程池','default','sys_job_executor','',NULL,0,NULL,1,23,1,'线程池','2025-09-06 01:12:22','2025-09-06 01:12:22'),(2,'进程池','processpool','sys_job_executor','',NULL,0,NULL,1,24,1,'进程池','2025-09-06 01:12:22','2025-09-06 01:12:22'),(1,'演示函数','scheduler_test.job','sys_job_function','',NULL,1,NULL,1,25,1,'演示函数','2025-09-06 01:12:22','2025-09-06 01:12:22'),(1,'指定日期(date)','date','sys_job_trigger','',NULL,1,NULL,1,26,1,'指定日期任务触发器','2025-09-06 01:12:22','2025-09-06 01:12:22'),(2,'间隔触发器(interval)','interval','sys_job_trigger','',NULL,0,NULL,1,27,1,'间隔触发器任务触发器','2025-09-06 01:12:22','2025-09-06 01:12:22'),(3,'cron表达式','cron','sys_job_trigger','',NULL,0,NULL,1,28,1,'间隔触发器任务触发器','2025-09-06 01:12:22','2025-09-06 01:12:22'),(1,'默认(default)','default','sys_list_class','',NULL,1,NULL,1,29,1,'默认表格回显样式','2025-09-06 01:12:22','2025-09-06 01:12:22'),(2,'主要(primary)','primary','sys_list_class','',NULL,0,NULL,1,30,1,'主要表格回显样式','2025-09-06 01:12:22','2025-09-06 01:12:22'),(3,'成功(success)','success','sys_list_class','',NULL,0,NULL,1,31,1,'成功表格回显样式','2025-09-06 01:12:22','2025-09-06 01:12:22'),(4,'信息(info)','info','sys_list_class','',NULL,0,NULL,1,32,1,'信息表格回显样式','2025-09-06 01:12:22','2025-09-06 01:12:22'),(5,'警告(warning)','warning','sys_list_class','',NULL,0,NULL,1,33,1,'警告表格回显样式','2025-09-06 01:12:22','2025-09-06 01:12:22'),(6,'危险(danger)','danger','sys_list_class','',NULL,0,NULL,1,34,1,'危险表格回显样式','2025-09-06 01:12:22','2025-09-06 01:12:22');
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
  `creator_id` int DEFAULT NULL COMMENT '创建人ID',
  `id` int NOT NULL AUTO_INCREMENT COMMENT '主键ID',
  `status` tinyint(1) NOT NULL COMMENT '是否启用(True:启用 False:禁用)',
  `description` text COMMENT '备注说明',
  `created_at` datetime NOT NULL COMMENT '创建时间',
  `updated_at` datetime NOT NULL COMMENT '更新时间',
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
INSERT INTO `system_dict_type` VALUES ('用户性别','sys_user_sex',1,1,1,'用户性别列表','2025-09-06 01:12:22','2025-09-06 01:12:22'),('系统是否','sys_yes_no',1,2,1,'系统是否列表','2025-09-06 01:12:22','2025-09-06 01:12:22'),('系统状态','sys_common_status',1,3,1,'系统状态','2025-09-06 01:12:22','2025-09-06 01:12:22'),('通知类型','sys_notice_type',1,4,1,'通知类型列表','2025-09-06 01:12:22','2025-09-06 01:12:22'),('操作类型','sys_oper_type',1,5,1,'操作类型列表','2025-09-06 01:12:22','2025-09-06 01:12:22'),('任务存储器','sys_job_store',1,6,1,'任务分组列表','2025-09-06 01:12:22','2025-09-06 01:12:22'),('任务执行器','sys_job_executor',1,7,1,'任务执行器列表','2025-09-06 01:12:22','2025-09-06 01:12:22'),('任务函数','sys_job_function',1,8,1,'任务函数列表','2025-09-06 01:12:22','2025-09-06 01:12:22'),('任务触发器','sys_job_trigger',1,9,1,'任务触发器列表','2025-09-06 01:12:22','2025-09-06 01:12:22'),('表格回显样式','sys_list_class',1,10,1,'表格回显样式列表','2025-09-06 01:12:22','2025-09-06 01:12:22');
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
  `status` tinyint(1) NOT NULL COMMENT '是否启用(True:启用 False:禁用)',
  `description` text COMMENT '备注说明',
  `created_at` datetime NOT NULL COMMENT '创建时间',
  `updated_at` datetime NOT NULL COMMENT '更新时间',
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
  `name` varchar(50) NOT NULL COMMENT '菜单名称',
  `type` int NOT NULL COMMENT '菜单类型(1:目录 2:菜单 3:按钮/权限 4:链接)',
  `order` int NOT NULL COMMENT '显示排序',
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
  `id` int NOT NULL AUTO_INCREMENT COMMENT '主键ID',
  `status` tinyint(1) NOT NULL COMMENT '是否启用(True:启用 False:禁用)',
  `description` text COMMENT '备注说明',
  `created_at` datetime NOT NULL COMMENT '创建时间',
  `updated_at` datetime NOT NULL COMMENT '更新时间',
  PRIMARY KEY (`id`),
  UNIQUE KEY `name` (`name`),
  KEY `ix_system_menu_parent_id` (`parent_id`),
  CONSTRAINT `system_menu_ibfk_1` FOREIGN KEY (`parent_id`) REFERENCES `system_menu` (`id`) ON DELETE SET NULL
) ENGINE=InnoDB AUTO_INCREMENT=102 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci COMMENT='菜单表';
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `system_menu`
--

/*!40000 ALTER TABLE `system_menu` DISABLE KEYS */;
INSERT INTO `system_menu` VALUES ('仪表盘',1,1,'','client','Dashboard','/dashboard',NULL,'/dashboard/workplace',0,1,1,'仪表盘','null',0,NULL,1,1,'初始化数据','2025-09-06 01:12:22','2025-09-06 01:12:22'),('工作台',2,1,'dashboard:workplace:query','homepage','Workplace','/dashboard/workplace','dashboard/workplace',NULL,0,1,0,'工作台','null',1,1,2,1,'初始化数据','2025-09-06 01:12:22','2025-09-06 01:12:22'),('分析页',2,2,'dashboard:analysis:query','el-icon-PieChart','Analysis','/dashboard/analysis','dashboard/analysis',NULL,0,1,0,'分析页','null',0,1,3,1,'初始化数据','2025-09-06 01:12:22','2025-09-06 01:12:22'),('系统管理',1,2,NULL,'system','System','/system',NULL,'/system/menu',0,1,0,'系统管理','null',0,NULL,4,1,'初始化数据','2025-09-06 01:12:22','2025-09-06 01:12:22'),('菜单管理',2,1,'system:menu:query','menu','Menu','/system/menu','system/menu/index',NULL,0,1,0,'菜单管理','null',0,4,5,1,'初始化数据','2025-09-06 01:12:22','2025-09-06 01:12:22'),('部门管理',2,2,'system:dept:query','tree','Dept','/system/dept','system/dept/index',NULL,0,1,0,'部门管理','null',0,4,6,1,'初始化数据','2025-09-06 01:12:22','2025-09-06 01:12:22'),('岗位管理',2,3,'system:position:query','el-icon-Coordinate','Position','/system/position','system/position/index',NULL,0,1,0,'岗位管理','null',0,4,7,1,'初始化数据','2025-09-06 01:12:22','2025-09-06 01:12:22'),('角色管理',2,4,'system:role:query','role','Role','/system/role','system/role/index',NULL,0,1,0,'角色管理','null',0,4,8,1,'初始化数据','2025-09-06 01:12:22','2025-09-06 01:12:22'),('用户管理',2,5,'system:user:query','el-icon-User','User','/system/user','system/user/index',NULL,0,1,0,'用户管理','null',0,4,9,1,'初始化数据','2025-09-06 01:12:22','2025-09-06 01:12:22'),('日志管理',2,6,'system:log:query','el-icon-Aim','Log','/system/log','system/log/index',NULL,0,1,0,'日志管理','null',0,4,10,1,'初始化数据','2025-09-06 01:12:22','2025-09-06 01:12:22'),('公告管理',2,7,'system:notice:query','bell','Notice','/system/notice','system/notice/index',NULL,0,1,0,'公告管理','null',0,4,11,1,'初始化数据','2025-09-06 01:12:22','2025-09-06 01:12:22'),('配置管理',2,8,'system:config:query','setting','Config','/system/config','system/config/index',NULL,0,1,0,'配置管理','null',0,4,12,1,'初始化数据','2025-09-06 01:12:22','2025-09-06 01:12:22'),('字典管理',2,9,'system:dict_type:query','dict','Dict','/system/dict','system/dict/index',NULL,0,1,0,'字典管理','null',0,4,13,1,'初始化数据','2025-09-06 01:12:22','2025-09-06 01:12:22'),('创建菜单',3,1,'system:menu:create',NULL,NULL,NULL,NULL,NULL,0,1,0,'创建菜单','null',0,5,14,1,'初始化数据','2025-09-06 01:12:22','2025-09-06 01:12:22'),('修改菜单',3,2,'system:menu:update',NULL,NULL,NULL,NULL,NULL,0,1,0,'修改菜单','null',0,5,15,1,'初始化数据','2025-09-06 01:12:22','2025-09-06 01:12:22'),('删除菜单',3,3,'system:menu:delete',NULL,NULL,NULL,NULL,NULL,0,1,0,'删除菜单','null',0,5,16,1,'初始化数据','2025-09-06 01:12:22','2025-09-06 01:12:22'),('批量修改菜单状态',3,4,'system:menu:patch',NULL,NULL,NULL,NULL,NULL,0,1,0,'批量修改菜单状态','null',0,5,17,1,'初始化数据','2025-09-06 01:12:22','2025-09-06 01:12:22'),('创建部门',3,1,'system:dept:create',NULL,NULL,NULL,NULL,NULL,0,1,0,'创建部门','null',0,6,18,1,'初始化数据','2025-09-06 01:12:22','2025-09-06 01:12:22'),('修改部门',3,2,'system:dept:update',NULL,NULL,NULL,NULL,NULL,0,1,0,'修改部门','null',0,6,19,1,'初始化数据','2025-09-06 01:12:22','2025-09-06 01:12:22'),('删除部门',3,3,'system:dept:delete',NULL,NULL,NULL,NULL,NULL,0,1,0,'删除部门','null',0,6,20,1,'初始化数据','2025-09-06 01:12:22','2025-09-06 01:12:22'),('批量修改部门状态',3,4,'system:dept:patch',NULL,NULL,NULL,NULL,NULL,0,1,0,'批量修改部门状态','null',0,6,21,1,'初始化数据','2025-09-06 01:12:22','2025-09-06 01:12:22'),('创建岗位',3,1,'system:position:create',NULL,NULL,NULL,NULL,NULL,0,1,0,'创建岗位','null',0,7,22,1,'初始化数据','2025-09-06 01:12:22','2025-09-06 01:12:22'),('修改岗位',3,2,'system:position:update',NULL,NULL,NULL,NULL,NULL,0,1,0,'修改岗位','null',0,7,23,1,'初始化数据','2025-09-06 01:12:22','2025-09-06 01:12:22'),('删除岗位',3,3,'system:position:delete',NULL,NULL,NULL,NULL,NULL,0,1,0,'修改岗位','null',0,7,24,1,'初始化数据','2025-09-06 01:12:22','2025-09-06 01:12:22'),('批量修改岗位状态',3,4,'system:position:patch',NULL,NULL,NULL,NULL,NULL,0,1,0,'批量修改岗位状态','null',0,7,25,1,'初始化数据','2025-09-06 01:12:22','2025-09-06 01:12:22'),('岗位导出',3,5,'system:position:export',NULL,NULL,NULL,NULL,NULL,0,1,0,'岗位导出','null',0,7,26,1,'初始化数据','2025-09-06 01:12:22','2025-09-06 01:12:22'),('创建角色',3,1,'system:role:create',NULL,NULL,NULL,NULL,NULL,0,1,0,'创建角色','null',0,8,27,1,'初始化数据','2025-09-06 01:12:22','2025-09-06 01:12:22'),('修改角色',3,2,'system:role:update',NULL,NULL,NULL,NULL,NULL,0,1,0,'修改角色','null',0,8,28,1,'初始化数据','2025-09-06 01:12:22','2025-09-06 01:12:22'),('删除角色',3,3,'system:role:delete',NULL,NULL,NULL,NULL,NULL,0,1,0,'删除角色','null',0,8,29,1,'初始化数据','2025-09-06 01:12:22','2025-09-06 01:12:22'),('批量修改角色状态',3,4,'system:role:patch',NULL,NULL,NULL,NULL,NULL,0,1,0,'批量修改角色状态','null',0,8,30,1,'初始化数据','2025-09-06 01:12:22','2025-09-06 01:12:22'),('设置角色权限',3,8,'system:role:permission',NULL,NULL,NULL,NULL,NULL,0,1,0,'设置角色权限','null',0,7,31,1,'初始化数据','2025-09-06 01:12:22','2025-09-06 01:12:22'),('角色导出',3,6,'system:role:export',NULL,NULL,NULL,NULL,NULL,0,1,0,'角色导出','null',0,8,32,1,'初始化数据','2025-09-06 01:12:22','2025-09-06 01:12:22'),('创建用户',3,1,'system:user:create',NULL,NULL,NULL,NULL,NULL,0,1,0,'创建用户','null',0,9,33,1,'初始化数据','2025-09-06 01:12:22','2025-09-06 01:12:22'),('修改用户',3,2,'system:user:update',NULL,NULL,NULL,NULL,NULL,0,1,0,'修改用户','null',0,9,34,1,'初始化数据','2025-09-06 01:12:22','2025-09-06 01:12:22'),('删除用户',3,3,'system:user:delete',NULL,NULL,NULL,NULL,NULL,0,1,0,'删除用户','null',0,9,35,1,'初始化数据','2025-09-06 01:12:22','2025-09-06 01:12:22'),('批量修改用户状态',3,4,'system:user:patch',NULL,NULL,NULL,NULL,NULL,0,1,0,'批量修改用户状态','null',0,9,36,1,'初始化数据','2025-09-06 01:12:22','2025-09-06 01:12:22'),('导出用户',3,5,'system:user:export',NULL,NULL,NULL,NULL,NULL,0,1,0,'导出用户','null',0,9,37,1,'初始化数据','2025-09-06 01:12:22','2025-09-06 01:12:22'),('导入用户',3,6,'system:user:import',NULL,NULL,NULL,NULL,NULL,0,1,0,'导入用户','null',0,9,38,1,'初始化数据','2025-09-06 01:12:22','2025-09-06 01:12:22'),('日志删除',3,1,'system:operation_log:delete',NULL,NULL,NULL,NULL,NULL,0,1,0,'日志删除','null',0,10,39,1,'初始化数据','2025-09-06 01:12:22','2025-09-06 01:12:22'),('日志导出',3,2,'system:operation_log:export',NULL,NULL,NULL,NULL,NULL,0,1,0,'日志导出','null',0,10,40,1,'初始化数据','2025-09-06 01:12:22','2025-09-06 01:12:22'),('公告创建',3,1,'system:notice:create',NULL,NULL,NULL,NULL,NULL,0,1,0,'公告创建','null',0,11,41,1,'初始化数据','2025-09-06 01:12:22','2025-09-06 01:12:22'),('公告修改',3,2,'system:notice:update',NULL,NULL,NULL,NULL,NULL,0,1,0,'修改用户','null',0,11,42,1,'初始化数据','2025-09-06 01:12:22','2025-09-06 01:12:22'),('公告删除',3,3,'system:notice:delete',NULL,NULL,NULL,NULL,NULL,0,1,0,'公告删除','null',0,11,43,1,'初始化数据','2025-09-06 01:12:22','2025-09-06 01:12:22'),('公告导出',3,4,'system:notice:export',NULL,NULL,NULL,NULL,NULL,0,1,0,'公告导出','null',0,11,44,1,'初始化数据','2025-09-06 01:12:22','2025-09-06 01:12:22'),('公告批量修改状态',3,5,'system:notice:patch',NULL,NULL,NULL,NULL,NULL,0,1,0,'公告批量修改状态','null',0,11,45,1,'初始化数据','2025-09-06 01:12:22','2025-09-06 01:12:22'),('创建配置',3,1,'system:config:create',NULL,NULL,NULL,NULL,NULL,0,1,0,'创建配置','null',0,12,46,1,'初始化数据','2025-09-06 01:12:22','2025-09-06 01:12:22'),('修改配置',3,2,'system:config:update',NULL,NULL,NULL,NULL,NULL,0,1,0,'修改配置','null',0,12,47,1,'初始化数据','2025-09-06 01:12:22','2025-09-06 01:12:22'),('删除配置',3,3,'system:config:delete',NULL,NULL,NULL,NULL,NULL,0,1,0,'删除配置','null',0,12,48,1,'初始化数据','2025-09-06 01:12:22','2025-09-06 01:12:22'),('导出配置',3,4,'system:config:export',NULL,NULL,NULL,NULL,NULL,0,1,0,'导出配置','null',0,12,49,1,'初始化数据','2025-09-06 01:12:22','2025-09-06 01:12:22'),('配置上传',3,5,'system:config:upload',NULL,NULL,NULL,NULL,NULL,0,1,0,'配置上传','null',0,12,50,1,'初始化数据','2025-09-06 01:12:22','2025-09-06 01:12:22'),('创建字典类型',3,1,'system:dict_type:create',NULL,NULL,NULL,NULL,NULL,0,1,0,'创建字典类型','null',0,13,51,1,'初始化数据','2025-09-06 01:12:22','2025-09-06 01:12:22'),('修改字典类型',3,2,'system:dict_type:update',NULL,NULL,NULL,NULL,NULL,0,1,0,'修改字典类型','null',0,13,52,1,'初始化数据','2025-09-06 01:12:22','2025-09-06 01:12:22'),('删除字典类型',3,3,'system:dict_type:delete',NULL,NULL,NULL,NULL,NULL,0,1,0,'删除字典类型','null',0,13,53,1,'初始化数据','2025-09-06 01:12:22','2025-09-06 01:12:22'),('导出字典类型',3,4,'system:dict_type:export',NULL,NULL,NULL,NULL,NULL,0,1,0,'导出字典类型','null',0,13,54,1,'初始化数据','2025-09-06 01:12:22','2025-09-06 01:12:22'),('批量修改字典状态',3,5,'system:dict_type:patch',NULL,NULL,NULL,NULL,NULL,0,1,0,'导出字典类型','null',0,13,55,1,'初始化数据','2025-09-06 01:12:22','2025-09-06 01:12:22'),('字典数据查询',3,6,'system:dict_data:query',NULL,NULL,NULL,NULL,NULL,0,1,0,'字典数据查询','null',0,13,56,1,'初始化数据','2025-09-06 01:12:22','2025-09-06 01:12:22'),('创建字典数据',3,7,'system:dict_data:create',NULL,NULL,NULL,NULL,NULL,0,1,0,'创建字典数据','null',0,13,57,1,'初始化数据','2025-09-06 01:12:22','2025-09-06 01:12:22'),('修改字典数据',3,8,'system:dict_data:update',NULL,NULL,NULL,NULL,NULL,0,1,0,'修改字典数据','null',0,13,58,1,'初始化数据','2025-09-06 01:12:22','2025-09-06 01:12:22'),('删除字典数据',3,9,'system:dict_data:delete',NULL,NULL,NULL,NULL,NULL,0,1,0,'删除字典数据','null',0,13,59,1,'初始化数据','2025-09-06 01:12:22','2025-09-06 01:12:22'),('导出字典数据',3,10,'system:dict_data:export',NULL,NULL,NULL,NULL,NULL,0,1,0,'导出字典数据','null',0,13,60,1,'初始化数据','2025-09-06 01:12:22','2025-09-06 01:12:22'),('批量修改字典数据状态',3,11,'system:dict_data:patch',NULL,NULL,NULL,NULL,NULL,0,1,0,'批量修改字典数据状态','null',0,13,61,1,'初始化数据','2025-09-06 01:12:22','2025-09-06 01:12:22'),('监控管理',1,3,NULL,'monitor','Monitor','/monitor',NULL,'/monitor/online',0,0,0,'监控管理','null',0,NULL,62,1,'初始化数据','2025-09-06 01:12:22','2025-09-06 01:12:22'),('任务管理',2,1,'monitor:job:query','el-icon-DataLine','Job','/monitor/job','monitor/job/index',NULL,0,1,0,'任务管理','null',0,62,63,1,'初始化数据','2025-09-06 01:12:22','2025-09-06 01:12:22'),('创建任务',3,1,'monitor:job:create',NULL,NULL,NULL,NULL,NULL,0,1,0,'创建任务','null',0,63,64,1,'初始化数据','2025-09-06 01:12:22','2025-09-06 01:12:22'),('修改和操作任务',3,2,'monitor:job:update',NULL,NULL,NULL,NULL,NULL,0,1,0,'修改和操作任务','null',0,63,65,1,'初始化数据','2025-09-06 01:12:22','2025-09-06 01:12:22'),('删除和清除任务',3,3,'monitor:job:delete',NULL,NULL,NULL,NULL,NULL,0,1,0,'删除和清除任务','null',0,63,66,1,'初始化数据','2025-09-06 01:12:22','2025-09-06 01:12:22'),('导出定时任务',3,4,'monitor:job:export',NULL,NULL,NULL,NULL,NULL,0,1,0,'导出定时任务','null',0,63,67,1,'初始化数据','2025-09-06 01:12:22','2025-09-06 01:12:22'),('在线用户',2,2,'monitor:online:query','el-icon-Headset','MonitorOnline','/monitor/online','monitor/online/index',NULL,0,0,0,'在线用户','null',0,62,68,1,'初始化数据','2025-09-06 01:12:22','2025-09-06 01:12:22'),('在线用户强制下线',3,1,'monitor:online:delete',NULL,NULL,NULL,NULL,NULL,0,0,0,'在线用户强制下线','null',0,68,69,1,'初始化数据','2025-09-06 01:12:22','2025-09-06 01:12:22'),('服务器监控',2,3,'monitor:server:query','el-icon-Odometer','MonitorServer','/monitor/server','monitor/server/index',NULL,0,0,0,'服务器监控','null',0,62,70,1,'初始化数据','2025-09-06 01:12:22','2025-09-06 01:12:22'),('缓存监控',2,4,'monitor:cache:query','el-icon-Stopwatch','MonitorCache','/monitor/cache','monitor/cache/index',NULL,0,0,0,'缓存监控','null',0,62,71,1,'初始化数据','2025-09-06 01:12:22','2025-09-06 01:12:22'),('清除缓存',3,1,'monitor:cache:delete',NULL,NULL,NULL,NULL,NULL,0,0,0,'清除缓存','null',0,71,72,1,'初始化数据','2025-09-06 01:12:22','2025-09-06 01:12:22'),('公共模块',1,4,NULL,'document','Common','/common',NULL,'/common/docs',0,0,0,'公共模块','null',0,NULL,73,1,'初始化数据','2025-09-06 01:12:22','2025-09-06 01:12:22'),('接口管理',4,1,'common:docs:query','api','Docs','/common/docs','common/docs/index',NULL,0,0,0,'接口管理','null',0,73,74,1,'初始化数据','2025-09-06 01:12:22','2025-09-06 01:12:22'),('文档管理',4,2,'common:redoc:query','el-icon-Document','Redoc','/common/redoc','common/redoc/index',NULL,0,0,0,'文档管理','null',0,73,75,1,'初始化数据','2025-09-06 01:12:22','2025-09-06 01:12:22'),('演示模块',1,5,NULL,'el-icon-Document','Demo','/demo',NULL,'/demo/example',0,0,0,'演示模块','null',0,NULL,76,1,'初始化数据','2025-09-06 01:12:22','2025-09-06 01:12:22'),('示例管理',2,1,'demo:example:query','el-icon-DataLine','Example','/demo/example','demo/example/index',NULL,0,1,0,'示例管理','null',0,76,77,1,'初始化数据','2025-09-06 01:12:22','2025-09-06 01:12:22'),('创建示例',3,1,'demo:example:create',NULL,NULL,NULL,NULL,NULL,0,1,0,'创建示例','null',0,77,78,1,'初始化数据','2025-09-06 01:12:22','2025-09-06 01:12:22'),('更新示例',3,2,'demo:example:update',NULL,NULL,NULL,NULL,NULL,0,1,0,'更新示例','null',0,77,79,1,'初始化数据','2025-09-06 01:12:22','2025-09-06 01:12:22'),('删除示例',3,3,'demo:example:delete',NULL,NULL,NULL,NULL,NULL,0,1,0,'删除示例','null',0,77,80,1,'初始化数据','2025-09-06 01:12:22','2025-09-06 01:12:22'),('批量修改示例状态',3,4,'demo:example:patch',NULL,NULL,NULL,NULL,NULL,0,1,0,'批量修改示例状态','null',0,77,81,1,'初始化数据','2025-09-06 01:12:22','2025-09-06 01:12:22'),('导出示例',3,5,'demo:example:export',NULL,NULL,NULL,NULL,NULL,0,1,0,'导出示例','null',0,77,82,1,'初始化数据','2025-09-06 01:12:22','2025-09-06 01:12:22'),('导入示例',3,6,'demo:example:import',NULL,NULL,NULL,NULL,NULL,0,1,0,'导入示例','null',0,77,83,1,'初始化数据','2025-09-06 01:12:22','2025-09-06 01:12:22'),('下载导入示例模版',3,7,'demo:example:download',NULL,NULL,NULL,NULL,NULL,0,1,0,'下载导入示例模版','null',0,77,84,1,'初始化数据','2025-09-06 01:12:22','2025-09-06 01:12:22'),('应用管理',1,6,NULL,'captcha','Application','/application',NULL,'/application/myapp',0,0,0,'应用管理','null',0,NULL,85,1,'初始化数据','2025-09-06 01:12:22','2025-09-06 01:12:22'),('我的应用',2,1,'application:myapp:query','el-icon-DataLine','ApplicationSystem','/application/myapp','application/myapp/index',NULL,0,1,0,'应用系统管理','null',0,85,86,1,'初始化数据','2025-09-06 01:12:22','2025-09-06 01:12:22'),('创建应用',3,1,'application:myapp:create',NULL,NULL,NULL,NULL,NULL,0,1,0,'创建应用','null',0,86,87,1,'初始化数据','2025-09-06 01:12:22','2025-09-06 01:12:22'),('修改应用',3,2,'application:myapp:update',NULL,NULL,NULL,NULL,NULL,0,1,0,'修改应用','null',0,86,88,1,'初始化数据','2025-09-06 01:12:22','2025-09-06 01:12:22'),('删除应用',3,3,'application:myapp:delete',NULL,NULL,NULL,NULL,NULL,0,1,0,'删除应用','null',0,86,89,1,'初始化数据','2025-09-06 01:12:22','2025-09-06 01:12:22'),('批量修改应用状态',3,4,'application:myapp:patch',NULL,NULL,NULL,NULL,NULL,0,1,0,'批量修改应用状态','null',0,86,90,1,'初始化数据','2025-09-06 01:12:22','2025-09-06 01:12:22'),('资源管理',1,7,NULL,'document','Resource','/resource',NULL,'/resource/file',0,0,0,'资源管理','null',0,NULL,91,1,'初始化数据','2025-09-06 01:12:22','2025-09-06 01:12:22'),('文件管理',2,1,'resource:file:query','el-icon-Files','ResourceFile','/resource/file','resource/file/index',NULL,0,1,0,'文件管理','null',0,91,92,1,'初始化数据','2025-09-06 01:12:22','2025-09-06 01:12:22'),('文件上传',3,1,'resource:file:upload',NULL,NULL,NULL,NULL,NULL,0,1,0,'文件上传','null',0,92,93,1,'初始化数据','2025-09-06 01:12:22','2025-09-06 01:12:22'),('文件下载',3,2,'resource:file:download',NULL,NULL,NULL,NULL,NULL,0,1,0,'文件下载','null',0,92,94,1,'初始化数据','2025-09-06 01:12:22','2025-09-06 01:12:22'),('文件删除',3,3,'resource:file:delete',NULL,NULL,NULL,NULL,NULL,0,1,0,'文件删除','null',0,92,95,1,'初始化数据','2025-09-06 01:12:22','2025-09-06 01:12:22'),('文件移动',3,4,'resource:file:move',NULL,NULL,NULL,NULL,NULL,0,1,0,'文件移动','null',0,92,96,1,'初始化数据','2025-09-06 01:12:22','2025-09-06 01:12:22'),('文件复制',3,5,'resource:file:copy',NULL,NULL,NULL,NULL,NULL,0,1,0,'文件复制','null',0,92,97,1,'初始化数据','2025-09-06 01:12:22','2025-09-06 01:12:22'),('文件重命名',3,6,'resource:file:rename',NULL,NULL,NULL,NULL,NULL,0,1,0,'文件重命名','null',0,92,98,1,'初始化数据','2025-09-06 01:12:22','2025-09-06 01:12:22'),('创建目录',3,7,'resource:file:create_dir',NULL,NULL,NULL,NULL,NULL,0,1,0,'创建目录','null',0,92,99,1,'初始化数据','2025-09-06 01:12:22','2025-09-06 01:12:22'),('文件搜索',3,8,'resource:file:search',NULL,NULL,NULL,NULL,NULL,0,1,0,'文件搜索','null',0,92,100,1,'初始化数据','2025-09-06 01:12:22','2025-09-06 01:12:22'),('导出文件列表',3,9,'resource:file:export',NULL,NULL,NULL,NULL,NULL,0,1,0,'导出文件列表','null',0,92,101,1,'初始化数据','2025-09-06 01:12:22','2025-09-06 01:12:22');
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
  `creator_id` int DEFAULT NULL COMMENT '创建人ID',
  `id` int NOT NULL AUTO_INCREMENT COMMENT '主键ID',
  `status` tinyint(1) NOT NULL COMMENT '是否启用(True:启用 False:禁用)',
  `description` text COMMENT '备注说明',
  `created_at` datetime NOT NULL COMMENT '创建时间',
  `updated_at` datetime NOT NULL COMMENT '更新时间',
  PRIMARY KEY (`id`),
  KEY `ix_system_notice_creator_id` (`creator_id`)
) ENGINE=InnoDB AUTO_INCREMENT=5 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci COMMENT='通知公告表';
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `system_notice`
--

/*!40000 ALTER TABLE `system_notice` DISABLE KEYS */;
INSERT INTO `system_notice` VALUES ('系统更新','1','2099年9月9日，晚上12:00，系统更新',1,1,1,'系统更新','2025-09-06 01:12:22','2025-09-06 01:12:22'),('系统维护','2','2099年9月9日，晚上12:00，系统维护',1,2,1,'系统维护','2025-09-06 01:12:22','2025-09-06 01:12:22'),('系统更新完成','1','2099年9月9日，晚上12:00，系统更新完成',1,3,0,'系统更新完成','2025-09-06 01:12:22','2025-09-06 01:12:22'),('系统维护完成','2','2099年9月9日，晚上12:00，系统维护完成',1,4,0,'系统维护完成','2025-09-06 01:12:22','2025-09-06 01:12:22');
/*!40000 ALTER TABLE `system_notice` ENABLE KEYS */;

--
-- Table structure for table `system_position`
--

DROP TABLE IF EXISTS `system_position`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `system_position` (
  `name` varchar(40) NOT NULL COMMENT '岗位名称',
  `order` int NOT NULL COMMENT '显示排序',
  `creator_id` int DEFAULT NULL COMMENT '创建人ID',
  `id` int NOT NULL AUTO_INCREMENT COMMENT '主键ID',
  `status` tinyint(1) NOT NULL COMMENT '是否启用(True:启用 False:禁用)',
  `description` text COMMENT '备注说明',
  `created_at` datetime NOT NULL COMMENT '创建时间',
  `updated_at` datetime NOT NULL COMMENT '更新时间',
  PRIMARY KEY (`id`),
  UNIQUE KEY `name` (`name`),
  KEY `ix_system_position_creator_id` (`creator_id`)
) ENGINE=InnoDB AUTO_INCREMENT=8 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci COMMENT='岗位表';
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `system_position`
--

/*!40000 ALTER TABLE `system_position` DISABLE KEYS */;
INSERT INTO `system_position` VALUES ('董事长岗',1,1,1,1,'董事长岗位','2025-09-06 01:12:22','2025-09-06 01:12:22'),('运营岗',2,1,2,1,'运营岗位','2025-09-06 01:12:22','2025-09-06 01:12:22'),('销售岗',3,1,3,1,'销售岗','2025-09-06 01:12:22','2025-09-06 01:12:22'),('人事行政岗',4,1,4,1,'人事行政岗','2025-09-06 01:12:22','2025-09-06 01:12:22'),('开发岗',5,1,5,1,'开发岗','2025-09-06 01:12:22','2025-09-06 01:12:22'),('测试岗',6,1,6,1,'测试岗','2025-09-06 01:12:22','2025-09-06 01:12:22'),('演示岗',7,1,7,1,'演示岗','2025-09-06 01:12:22','2025-09-06 01:12:22');
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
  `data_scope` int NOT NULL COMMENT '数据权限范围',
  `creator_id` int DEFAULT NULL COMMENT '创建人ID',
  `id` int NOT NULL AUTO_INCREMENT COMMENT '主键ID',
  `status` tinyint(1) NOT NULL COMMENT '是否启用(True:启用 False:禁用)',
  `description` text COMMENT '备注说明',
  `created_at` datetime NOT NULL COMMENT '创建时间',
  `updated_at` datetime NOT NULL COMMENT '更新时间',
  PRIMARY KEY (`id`),
  UNIQUE KEY `name` (`name`),
  UNIQUE KEY `code` (`code`),
  KEY `ix_system_role_creator_id` (`creator_id`)
) ENGINE=InnoDB AUTO_INCREMENT=3 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci COMMENT='角色表';
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `system_role`
--

/*!40000 ALTER TABLE `system_role` DISABLE KEYS */;
INSERT INTO `system_role` VALUES ('管理员角色',NULL,1,4,1,1,1,'管理员','2025-09-06 01:12:22','2025-09-06 01:12:22'),('普通角色',NULL,2,1,1,2,1,'普通角色','2025-09-06 01:12:22','2025-09-06 01:12:22');
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
INSERT INTO `system_role_depts` VALUES (1,1),(2,1),(2,6);
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
INSERT INTO `system_role_menus` VALUES (1,1),(2,1),(1,2),(2,2),(1,3),(1,4),(1,5),(1,6),(1,7),(1,8),(1,9),(1,10),(1,11),(1,12),(1,13),(1,14),(1,15),(1,16),(1,17),(1,18),(1,19),(1,20),(1,21),(1,22),(1,23),(1,24),(1,25),(1,26),(1,27),(1,28),(1,29),(1,30),(1,31),(1,32),(1,33),(1,34),(1,35),(1,36),(1,37),(1,38),(1,39),(1,40),(1,41),(1,42),(1,43),(1,44),(1,45),(1,46),(1,47),(1,48),(1,49),(1,50),(1,51),(1,52),(1,53),(1,54),(1,55),(1,56),(1,57),(1,58),(1,59),(1,60),(1,61),(1,62),(1,63),(1,64),(1,65),(1,66),(1,67),(1,68),(1,69),(1,70),(1,71),(1,72),(1,73),(1,74),(1,75),(1,76),(1,77),(1,78),(1,79),(1,80),(1,81),(1,82),(1,83),(1,84),(1,85),(1,86),(1,87),(1,88),(1,89),(1,90),(1,91),(1,92),(1,93),(1,94),(1,95),(1,96),(1,97),(1,98),(1,99),(1,100),(1,101);
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
INSERT INTO `system_user_positions` VALUES (3,1),(1,5),(2,7);
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
INSERT INTO `system_user_roles` VALUES (1,1),(2,1),(3,1);
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
  `mobile` varchar(20) DEFAULT NULL COMMENT '手机号',
  `email` varchar(64) DEFAULT NULL COMMENT '邮箱',
  `gender` varchar(1) DEFAULT NULL COMMENT '性别(0:男 1:女 2:未知)',
  `avatar` varchar(500) DEFAULT NULL COMMENT '头像URL地址',
  `is_superuser` tinyint(1) NOT NULL COMMENT '是否超管',
  `last_login` datetime DEFAULT NULL COMMENT '最后登录时间',
  `dept_id` int DEFAULT NULL COMMENT '部门ID',
  `creator_id` int DEFAULT NULL COMMENT '创建人ID',
  `id` int NOT NULL AUTO_INCREMENT COMMENT '主键ID',
  `status` tinyint(1) NOT NULL COMMENT '是否启用(True:启用 False:禁用)',
  `description` text COMMENT '备注说明',
  `created_at` datetime NOT NULL COMMENT '创建时间',
  `updated_at` datetime NOT NULL COMMENT '更新时间',
  PRIMARY KEY (`id`),
  UNIQUE KEY `username` (`username`),
  UNIQUE KEY `mobile` (`mobile`),
  UNIQUE KEY `email` (`email`),
  KEY `ix_system_users_creator_id` (`creator_id`),
  KEY `ix_system_users_dept_id` (`dept_id`),
  CONSTRAINT `system_users_ibfk_1` FOREIGN KEY (`dept_id`) REFERENCES `system_dept` (`id`) ON DELETE SET NULL ON UPDATE CASCADE
) ENGINE=InnoDB AUTO_INCREMENT=4 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci COMMENT='用户表';
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `system_users`
--

/*!40000 ALTER TABLE `system_users` DISABLE KEYS */;
INSERT INTO `system_users` VALUES ('superadmin','$2b$12$/Df5YczDGF41zCh2F8Xbu.yHTJXGm3tONgsXz1KLUdG0mtpKUOLD2','超级管理员','15382112620','948080782@qq.com','1','https://service.fastapiadmin.com/api/v1/static/image/avatar.png',1,NULL,1,NULL,1,1,'超级管理员','2025-09-06 01:12:22','2025-09-06 01:12:22'),('admin','$2b$12$e2IJgS/cvHgJ0H3G7Xa08OXoXnk6N/NX3IZRtubBDElA0VLZhkNOa','管理员','15382112222','admin@qq.com','0','https://service.fastapiadmin.com/api/v1/static/image/avatar.png',0,NULL,1,1,2,1,'管理员','2025-09-06 01:12:22','2025-09-06 01:12:22'),('demo','$2b$12$e2IJgS/cvHgJ0H3G7Xa08OXoXnk6N/NX3IZRtubBDElA0VLZhkNOa','演示用户','15382112121','demo@qq.com','1','https://service.fastapiadmin.com/api/v1/static/image/avatar.png',0,NULL,6,1,3,1,'演示用户','2025-09-06 01:12:22','2025-09-06 01:12:22');
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

-- Dump completed on 2025-09-06  1:14:17
