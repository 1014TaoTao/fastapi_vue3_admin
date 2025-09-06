--
-- PostgreSQL database dump
--

-- Dumped from database version 17.5 (ServBay)
-- Dumped by pg_dump version 17.5 (ServBay)

SET statement_timeout = 0;
SET lock_timeout = 0;
SET idle_in_transaction_session_timeout = 0;
SET transaction_timeout = 0;
SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;
SELECT pg_catalog.set_config('search_path', '', false);
SET check_function_bodies = false;
SET xmloption = content;
SET client_min_messages = warning;
SET row_security = off;

SET default_tablespace = '';

SET default_table_access_method = heap;

--
-- Name: application_myapp; Type: TABLE; Schema: public; Owner: tao
--

CREATE TABLE public.application_myapp (
    name character varying(64) NOT NULL,
    access_url character varying(500) NOT NULL,
    icon_url character varying(300),
    creator_id integer,
    id integer NOT NULL,
    status boolean NOT NULL,
    description text,
    created_at timestamp without time zone NOT NULL,
    updated_at timestamp without time zone NOT NULL
);


ALTER TABLE public.application_myapp OWNER TO tao;

--
-- Name: TABLE application_myapp; Type: COMMENT; Schema: public; Owner: tao
--

COMMENT ON TABLE public.application_myapp IS '应用系统表';


--
-- Name: COLUMN application_myapp.name; Type: COMMENT; Schema: public; Owner: tao
--

COMMENT ON COLUMN public.application_myapp.name IS '应用名称';


--
-- Name: COLUMN application_myapp.access_url; Type: COMMENT; Schema: public; Owner: tao
--

COMMENT ON COLUMN public.application_myapp.access_url IS '访问地址';


--
-- Name: COLUMN application_myapp.icon_url; Type: COMMENT; Schema: public; Owner: tao
--

COMMENT ON COLUMN public.application_myapp.icon_url IS '应用图标URL';


--
-- Name: COLUMN application_myapp.creator_id; Type: COMMENT; Schema: public; Owner: tao
--

COMMENT ON COLUMN public.application_myapp.creator_id IS '创建人ID';


--
-- Name: COLUMN application_myapp.id; Type: COMMENT; Schema: public; Owner: tao
--

COMMENT ON COLUMN public.application_myapp.id IS '主键ID';


--
-- Name: COLUMN application_myapp.status; Type: COMMENT; Schema: public; Owner: tao
--

COMMENT ON COLUMN public.application_myapp.status IS '是否启用(True:启用 False:禁用)';


--
-- Name: COLUMN application_myapp.description; Type: COMMENT; Schema: public; Owner: tao
--

COMMENT ON COLUMN public.application_myapp.description IS '备注说明';


--
-- Name: COLUMN application_myapp.created_at; Type: COMMENT; Schema: public; Owner: tao
--

COMMENT ON COLUMN public.application_myapp.created_at IS '创建时间';


--
-- Name: COLUMN application_myapp.updated_at; Type: COMMENT; Schema: public; Owner: tao
--

COMMENT ON COLUMN public.application_myapp.updated_at IS '更新时间';


--
-- Name: application_myapp_id_seq; Type: SEQUENCE; Schema: public; Owner: tao
--

CREATE SEQUENCE public.application_myapp_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.application_myapp_id_seq OWNER TO tao;

--
-- Name: application_myapp_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: tao
--

ALTER SEQUENCE public.application_myapp_id_seq OWNED BY public.application_myapp.id;


--
-- Name: example_demo; Type: TABLE; Schema: public; Owner: tao
--

CREATE TABLE public.example_demo (
    name character varying(64),
    creator_id integer,
    id integer NOT NULL,
    status boolean NOT NULL,
    description text,
    created_at timestamp without time zone NOT NULL,
    updated_at timestamp without time zone NOT NULL
);


ALTER TABLE public.example_demo OWNER TO tao;

--
-- Name: TABLE example_demo; Type: COMMENT; Schema: public; Owner: tao
--

COMMENT ON TABLE public.example_demo IS '示例表';


--
-- Name: COLUMN example_demo.name; Type: COMMENT; Schema: public; Owner: tao
--

COMMENT ON COLUMN public.example_demo.name IS '名称';


--
-- Name: COLUMN example_demo.creator_id; Type: COMMENT; Schema: public; Owner: tao
--

COMMENT ON COLUMN public.example_demo.creator_id IS '创建人ID';


--
-- Name: COLUMN example_demo.id; Type: COMMENT; Schema: public; Owner: tao
--

COMMENT ON COLUMN public.example_demo.id IS '主键ID';


--
-- Name: COLUMN example_demo.status; Type: COMMENT; Schema: public; Owner: tao
--

COMMENT ON COLUMN public.example_demo.status IS '是否启用(True:启用 False:禁用)';


--
-- Name: COLUMN example_demo.description; Type: COMMENT; Schema: public; Owner: tao
--

COMMENT ON COLUMN public.example_demo.description IS '备注说明';


--
-- Name: COLUMN example_demo.created_at; Type: COMMENT; Schema: public; Owner: tao
--

COMMENT ON COLUMN public.example_demo.created_at IS '创建时间';


--
-- Name: COLUMN example_demo.updated_at; Type: COMMENT; Schema: public; Owner: tao
--

COMMENT ON COLUMN public.example_demo.updated_at IS '更新时间';


--
-- Name: example_demo_id_seq; Type: SEQUENCE; Schema: public; Owner: tao
--

CREATE SEQUENCE public.example_demo_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.example_demo_id_seq OWNER TO tao;

--
-- Name: example_demo_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: tao
--

ALTER SEQUENCE public.example_demo_id_seq OWNED BY public.example_demo.id;


--
-- Name: monitor_job; Type: TABLE; Schema: public; Owner: tao
--

CREATE TABLE public.monitor_job (
    name character varying(64),
    jobstore character varying(64),
    executor character varying(64),
    trigger character varying(64) NOT NULL,
    trigger_args text,
    func text NOT NULL,
    args text,
    kwargs text,
    "coalesce" boolean,
    max_instances integer,
    start_date character varying(64),
    end_date character varying(64),
    creator_id integer,
    id integer NOT NULL,
    status boolean NOT NULL,
    description text,
    created_at timestamp without time zone NOT NULL,
    updated_at timestamp without time zone NOT NULL
);


ALTER TABLE public.monitor_job OWNER TO tao;

--
-- Name: TABLE monitor_job; Type: COMMENT; Schema: public; Owner: tao
--

COMMENT ON TABLE public.monitor_job IS '定时任务调度表';


--
-- Name: COLUMN monitor_job.name; Type: COMMENT; Schema: public; Owner: tao
--

COMMENT ON COLUMN public.monitor_job.name IS '任务名称';


--
-- Name: COLUMN monitor_job.jobstore; Type: COMMENT; Schema: public; Owner: tao
--

COMMENT ON COLUMN public.monitor_job.jobstore IS '存储器';


--
-- Name: COLUMN monitor_job.executor; Type: COMMENT; Schema: public; Owner: tao
--

COMMENT ON COLUMN public.monitor_job.executor IS '执行器:将运行此作业的执行程序的名称';


--
-- Name: COLUMN monitor_job.trigger; Type: COMMENT; Schema: public; Owner: tao
--

COMMENT ON COLUMN public.monitor_job.trigger IS '触发器:控制此作业计划的 trigger 对象';


--
-- Name: COLUMN monitor_job.trigger_args; Type: COMMENT; Schema: public; Owner: tao
--

COMMENT ON COLUMN public.monitor_job.trigger_args IS '触发器参数';


--
-- Name: COLUMN monitor_job.func; Type: COMMENT; Schema: public; Owner: tao
--

COMMENT ON COLUMN public.monitor_job.func IS '任务函数';


--
-- Name: COLUMN monitor_job.args; Type: COMMENT; Schema: public; Owner: tao
--

COMMENT ON COLUMN public.monitor_job.args IS '位置参数';


--
-- Name: COLUMN monitor_job.kwargs; Type: COMMENT; Schema: public; Owner: tao
--

COMMENT ON COLUMN public.monitor_job.kwargs IS '关键字参数';


--
-- Name: COLUMN monitor_job."coalesce"; Type: COMMENT; Schema: public; Owner: tao
--

COMMENT ON COLUMN public.monitor_job."coalesce" IS '是否合并运行:是否在多个运行时间到期时仅运行作业一次';


--
-- Name: COLUMN monitor_job.max_instances; Type: COMMENT; Schema: public; Owner: tao
--

COMMENT ON COLUMN public.monitor_job.max_instances IS '最大实例数:允许的最大并发执行实例数 工作';


--
-- Name: COLUMN monitor_job.start_date; Type: COMMENT; Schema: public; Owner: tao
--

COMMENT ON COLUMN public.monitor_job.start_date IS '开始时间';


--
-- Name: COLUMN monitor_job.end_date; Type: COMMENT; Schema: public; Owner: tao
--

COMMENT ON COLUMN public.monitor_job.end_date IS '结束时间';


--
-- Name: COLUMN monitor_job.creator_id; Type: COMMENT; Schema: public; Owner: tao
--

COMMENT ON COLUMN public.monitor_job.creator_id IS '创建人ID';


--
-- Name: COLUMN monitor_job.id; Type: COMMENT; Schema: public; Owner: tao
--

COMMENT ON COLUMN public.monitor_job.id IS '主键ID';


--
-- Name: COLUMN monitor_job.status; Type: COMMENT; Schema: public; Owner: tao
--

COMMENT ON COLUMN public.monitor_job.status IS '是否启用(True:启用 False:禁用)';


--
-- Name: COLUMN monitor_job.description; Type: COMMENT; Schema: public; Owner: tao
--

COMMENT ON COLUMN public.monitor_job.description IS '备注说明';


--
-- Name: COLUMN monitor_job.created_at; Type: COMMENT; Schema: public; Owner: tao
--

COMMENT ON COLUMN public.monitor_job.created_at IS '创建时间';


--
-- Name: COLUMN monitor_job.updated_at; Type: COMMENT; Schema: public; Owner: tao
--

COMMENT ON COLUMN public.monitor_job.updated_at IS '更新时间';


--
-- Name: monitor_job_id_seq; Type: SEQUENCE; Schema: public; Owner: tao
--

CREATE SEQUENCE public.monitor_job_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.monitor_job_id_seq OWNER TO tao;

--
-- Name: monitor_job_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: tao
--

ALTER SEQUENCE public.monitor_job_id_seq OWNED BY public.monitor_job.id;


--
-- Name: monitor_job_log; Type: TABLE; Schema: public; Owner: tao
--

CREATE TABLE public.monitor_job_log (
    id integer NOT NULL,
    job_name character varying(64) NOT NULL,
    job_group character varying(64) NOT NULL,
    job_executor character varying(64) NOT NULL,
    invoke_target character varying(500) NOT NULL,
    job_args character varying(255),
    job_kwargs character varying(255),
    job_trigger character varying(255),
    job_message character varying(500),
    exception_info character varying(2000),
    job_id integer
);


ALTER TABLE public.monitor_job_log OWNER TO tao;

--
-- Name: TABLE monitor_job_log; Type: COMMENT; Schema: public; Owner: tao
--

COMMENT ON TABLE public.monitor_job_log IS '定时任务调度日志表';


--
-- Name: COLUMN monitor_job_log.id; Type: COMMENT; Schema: public; Owner: tao
--

COMMENT ON COLUMN public.monitor_job_log.id IS '主键ID';


--
-- Name: COLUMN monitor_job_log.job_name; Type: COMMENT; Schema: public; Owner: tao
--

COMMENT ON COLUMN public.monitor_job_log.job_name IS '任务名称';


--
-- Name: COLUMN monitor_job_log.job_group; Type: COMMENT; Schema: public; Owner: tao
--

COMMENT ON COLUMN public.monitor_job_log.job_group IS '任务组名';


--
-- Name: COLUMN monitor_job_log.job_executor; Type: COMMENT; Schema: public; Owner: tao
--

COMMENT ON COLUMN public.monitor_job_log.job_executor IS '任务执行器';


--
-- Name: COLUMN monitor_job_log.invoke_target; Type: COMMENT; Schema: public; Owner: tao
--

COMMENT ON COLUMN public.monitor_job_log.invoke_target IS '调用目标字符串';


--
-- Name: COLUMN monitor_job_log.job_args; Type: COMMENT; Schema: public; Owner: tao
--

COMMENT ON COLUMN public.monitor_job_log.job_args IS '位置参数';


--
-- Name: COLUMN monitor_job_log.job_kwargs; Type: COMMENT; Schema: public; Owner: tao
--

COMMENT ON COLUMN public.monitor_job_log.job_kwargs IS '关键字参数';


--
-- Name: COLUMN monitor_job_log.job_trigger; Type: COMMENT; Schema: public; Owner: tao
--

COMMENT ON COLUMN public.monitor_job_log.job_trigger IS '任务触发器';


--
-- Name: COLUMN monitor_job_log.job_message; Type: COMMENT; Schema: public; Owner: tao
--

COMMENT ON COLUMN public.monitor_job_log.job_message IS '日志信息';


--
-- Name: COLUMN monitor_job_log.exception_info; Type: COMMENT; Schema: public; Owner: tao
--

COMMENT ON COLUMN public.monitor_job_log.exception_info IS '异常信息';


--
-- Name: COLUMN monitor_job_log.job_id; Type: COMMENT; Schema: public; Owner: tao
--

COMMENT ON COLUMN public.monitor_job_log.job_id IS '任务ID';


--
-- Name: monitor_job_log_id_seq; Type: SEQUENCE; Schema: public; Owner: tao
--

CREATE SEQUENCE public.monitor_job_log_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.monitor_job_log_id_seq OWNER TO tao;

--
-- Name: monitor_job_log_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: tao
--

ALTER SEQUENCE public.monitor_job_log_id_seq OWNED BY public.monitor_job_log.id;


--
-- Name: system_config; Type: TABLE; Schema: public; Owner: tao
--

CREATE TABLE public.system_config (
    config_name character varying(500) NOT NULL,
    config_key character varying(500) NOT NULL,
    config_value character varying(500),
    config_type boolean,
    creator_id integer,
    id integer NOT NULL,
    status boolean NOT NULL,
    description text,
    created_at timestamp without time zone NOT NULL,
    updated_at timestamp without time zone NOT NULL
);


ALTER TABLE public.system_config OWNER TO tao;

--
-- Name: TABLE system_config; Type: COMMENT; Schema: public; Owner: tao
--

COMMENT ON TABLE public.system_config IS '系统配置表';


--
-- Name: COLUMN system_config.config_name; Type: COMMENT; Schema: public; Owner: tao
--

COMMENT ON COLUMN public.system_config.config_name IS '参数名称';


--
-- Name: COLUMN system_config.config_key; Type: COMMENT; Schema: public; Owner: tao
--

COMMENT ON COLUMN public.system_config.config_key IS '参数键名';


--
-- Name: COLUMN system_config.config_value; Type: COMMENT; Schema: public; Owner: tao
--

COMMENT ON COLUMN public.system_config.config_value IS '参数键值';


--
-- Name: COLUMN system_config.config_type; Type: COMMENT; Schema: public; Owner: tao
--

COMMENT ON COLUMN public.system_config.config_type IS '系统内置(True:是 False:否)';


--
-- Name: COLUMN system_config.creator_id; Type: COMMENT; Schema: public; Owner: tao
--

COMMENT ON COLUMN public.system_config.creator_id IS '创建人ID';


--
-- Name: COLUMN system_config.id; Type: COMMENT; Schema: public; Owner: tao
--

COMMENT ON COLUMN public.system_config.id IS '主键ID';


--
-- Name: COLUMN system_config.status; Type: COMMENT; Schema: public; Owner: tao
--

COMMENT ON COLUMN public.system_config.status IS '是否启用(True:启用 False:禁用)';


--
-- Name: COLUMN system_config.description; Type: COMMENT; Schema: public; Owner: tao
--

COMMENT ON COLUMN public.system_config.description IS '备注说明';


--
-- Name: COLUMN system_config.created_at; Type: COMMENT; Schema: public; Owner: tao
--

COMMENT ON COLUMN public.system_config.created_at IS '创建时间';


--
-- Name: COLUMN system_config.updated_at; Type: COMMENT; Schema: public; Owner: tao
--

COMMENT ON COLUMN public.system_config.updated_at IS '更新时间';


--
-- Name: system_config_id_seq; Type: SEQUENCE; Schema: public; Owner: tao
--

CREATE SEQUENCE public.system_config_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.system_config_id_seq OWNER TO tao;

--
-- Name: system_config_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: tao
--

ALTER SEQUENCE public.system_config_id_seq OWNED BY public.system_config.id;


--
-- Name: system_dept; Type: TABLE; Schema: public; Owner: tao
--

CREATE TABLE public.system_dept (
    name character varying(40) NOT NULL,
    "order" integer NOT NULL,
    parent_id integer,
    id integer NOT NULL,
    status boolean NOT NULL,
    description text,
    created_at timestamp without time zone NOT NULL,
    updated_at timestamp without time zone NOT NULL
);


ALTER TABLE public.system_dept OWNER TO tao;

--
-- Name: TABLE system_dept; Type: COMMENT; Schema: public; Owner: tao
--

COMMENT ON TABLE public.system_dept IS '部门表';


--
-- Name: COLUMN system_dept.name; Type: COMMENT; Schema: public; Owner: tao
--

COMMENT ON COLUMN public.system_dept.name IS '部门名称';


--
-- Name: COLUMN system_dept."order"; Type: COMMENT; Schema: public; Owner: tao
--

COMMENT ON COLUMN public.system_dept."order" IS '显示排序';


--
-- Name: COLUMN system_dept.parent_id; Type: COMMENT; Schema: public; Owner: tao
--

COMMENT ON COLUMN public.system_dept.parent_id IS '父级部门ID';


--
-- Name: COLUMN system_dept.id; Type: COMMENT; Schema: public; Owner: tao
--

COMMENT ON COLUMN public.system_dept.id IS '主键ID';


--
-- Name: COLUMN system_dept.status; Type: COMMENT; Schema: public; Owner: tao
--

COMMENT ON COLUMN public.system_dept.status IS '是否启用(True:启用 False:禁用)';


--
-- Name: COLUMN system_dept.description; Type: COMMENT; Schema: public; Owner: tao
--

COMMENT ON COLUMN public.system_dept.description IS '备注说明';


--
-- Name: COLUMN system_dept.created_at; Type: COMMENT; Schema: public; Owner: tao
--

COMMENT ON COLUMN public.system_dept.created_at IS '创建时间';


--
-- Name: COLUMN system_dept.updated_at; Type: COMMENT; Schema: public; Owner: tao
--

COMMENT ON COLUMN public.system_dept.updated_at IS '更新时间';


--
-- Name: system_dept_id_seq; Type: SEQUENCE; Schema: public; Owner: tao
--

CREATE SEQUENCE public.system_dept_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.system_dept_id_seq OWNER TO tao;

--
-- Name: system_dept_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: tao
--

ALTER SEQUENCE public.system_dept_id_seq OWNED BY public.system_dept.id;


--
-- Name: system_dict_data; Type: TABLE; Schema: public; Owner: tao
--

CREATE TABLE public.system_dict_data (
    dict_sort integer NOT NULL,
    dict_label character varying(100) NOT NULL,
    dict_value character varying(100) NOT NULL,
    dict_type character varying(100) NOT NULL,
    css_class character varying(100),
    list_class character varying(100),
    is_default boolean NOT NULL,
    dict_type_id integer,
    creator_id integer,
    id integer NOT NULL,
    status boolean NOT NULL,
    description text,
    created_at timestamp without time zone NOT NULL,
    updated_at timestamp without time zone NOT NULL
);


ALTER TABLE public.system_dict_data OWNER TO tao;

--
-- Name: TABLE system_dict_data; Type: COMMENT; Schema: public; Owner: tao
--

COMMENT ON TABLE public.system_dict_data IS '字典数据表';


--
-- Name: COLUMN system_dict_data.dict_sort; Type: COMMENT; Schema: public; Owner: tao
--

COMMENT ON COLUMN public.system_dict_data.dict_sort IS '字典排序';


--
-- Name: COLUMN system_dict_data.dict_label; Type: COMMENT; Schema: public; Owner: tao
--

COMMENT ON COLUMN public.system_dict_data.dict_label IS '字典标签';


--
-- Name: COLUMN system_dict_data.dict_value; Type: COMMENT; Schema: public; Owner: tao
--

COMMENT ON COLUMN public.system_dict_data.dict_value IS '字典键值';


--
-- Name: COLUMN system_dict_data.dict_type; Type: COMMENT; Schema: public; Owner: tao
--

COMMENT ON COLUMN public.system_dict_data.dict_type IS '字典类型';


--
-- Name: COLUMN system_dict_data.css_class; Type: COMMENT; Schema: public; Owner: tao
--

COMMENT ON COLUMN public.system_dict_data.css_class IS '样式属性（其他样式扩展）';


--
-- Name: COLUMN system_dict_data.list_class; Type: COMMENT; Schema: public; Owner: tao
--

COMMENT ON COLUMN public.system_dict_data.list_class IS '表格回显样式';


--
-- Name: COLUMN system_dict_data.is_default; Type: COMMENT; Schema: public; Owner: tao
--

COMMENT ON COLUMN public.system_dict_data.is_default IS '是否默认（True是 False否）';


--
-- Name: COLUMN system_dict_data.dict_type_id; Type: COMMENT; Schema: public; Owner: tao
--

COMMENT ON COLUMN public.system_dict_data.dict_type_id IS '字典类型ID';


--
-- Name: COLUMN system_dict_data.creator_id; Type: COMMENT; Schema: public; Owner: tao
--

COMMENT ON COLUMN public.system_dict_data.creator_id IS '创建人ID';


--
-- Name: COLUMN system_dict_data.id; Type: COMMENT; Schema: public; Owner: tao
--

COMMENT ON COLUMN public.system_dict_data.id IS '主键ID';


--
-- Name: COLUMN system_dict_data.status; Type: COMMENT; Schema: public; Owner: tao
--

COMMENT ON COLUMN public.system_dict_data.status IS '是否启用(True:启用 False:禁用)';


--
-- Name: COLUMN system_dict_data.description; Type: COMMENT; Schema: public; Owner: tao
--

COMMENT ON COLUMN public.system_dict_data.description IS '备注说明';


--
-- Name: COLUMN system_dict_data.created_at; Type: COMMENT; Schema: public; Owner: tao
--

COMMENT ON COLUMN public.system_dict_data.created_at IS '创建时间';


--
-- Name: COLUMN system_dict_data.updated_at; Type: COMMENT; Schema: public; Owner: tao
--

COMMENT ON COLUMN public.system_dict_data.updated_at IS '更新时间';


--
-- Name: system_dict_data_id_seq; Type: SEQUENCE; Schema: public; Owner: tao
--

CREATE SEQUENCE public.system_dict_data_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.system_dict_data_id_seq OWNER TO tao;

--
-- Name: system_dict_data_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: tao
--

ALTER SEQUENCE public.system_dict_data_id_seq OWNED BY public.system_dict_data.id;


--
-- Name: system_dict_type; Type: TABLE; Schema: public; Owner: tao
--

CREATE TABLE public.system_dict_type (
    dict_name character varying(100) NOT NULL,
    dict_type character varying(100) NOT NULL,
    creator_id integer,
    id integer NOT NULL,
    status boolean NOT NULL,
    description text,
    created_at timestamp without time zone NOT NULL,
    updated_at timestamp without time zone NOT NULL
);


ALTER TABLE public.system_dict_type OWNER TO tao;

--
-- Name: TABLE system_dict_type; Type: COMMENT; Schema: public; Owner: tao
--

COMMENT ON TABLE public.system_dict_type IS '字典类型表';


--
-- Name: COLUMN system_dict_type.dict_name; Type: COMMENT; Schema: public; Owner: tao
--

COMMENT ON COLUMN public.system_dict_type.dict_name IS '字典名称';


--
-- Name: COLUMN system_dict_type.dict_type; Type: COMMENT; Schema: public; Owner: tao
--

COMMENT ON COLUMN public.system_dict_type.dict_type IS '字典类型';


--
-- Name: COLUMN system_dict_type.creator_id; Type: COMMENT; Schema: public; Owner: tao
--

COMMENT ON COLUMN public.system_dict_type.creator_id IS '创建人ID';


--
-- Name: COLUMN system_dict_type.id; Type: COMMENT; Schema: public; Owner: tao
--

COMMENT ON COLUMN public.system_dict_type.id IS '主键ID';


--
-- Name: COLUMN system_dict_type.status; Type: COMMENT; Schema: public; Owner: tao
--

COMMENT ON COLUMN public.system_dict_type.status IS '是否启用(True:启用 False:禁用)';


--
-- Name: COLUMN system_dict_type.description; Type: COMMENT; Schema: public; Owner: tao
--

COMMENT ON COLUMN public.system_dict_type.description IS '备注说明';


--
-- Name: COLUMN system_dict_type.created_at; Type: COMMENT; Schema: public; Owner: tao
--

COMMENT ON COLUMN public.system_dict_type.created_at IS '创建时间';


--
-- Name: COLUMN system_dict_type.updated_at; Type: COMMENT; Schema: public; Owner: tao
--

COMMENT ON COLUMN public.system_dict_type.updated_at IS '更新时间';


--
-- Name: system_dict_type_id_seq; Type: SEQUENCE; Schema: public; Owner: tao
--

CREATE SEQUENCE public.system_dict_type_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.system_dict_type_id_seq OWNER TO tao;

--
-- Name: system_dict_type_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: tao
--

ALTER SEQUENCE public.system_dict_type_id_seq OWNED BY public.system_dict_type.id;


--
-- Name: system_log; Type: TABLE; Schema: public; Owner: tao
--

CREATE TABLE public.system_log (
    type integer NOT NULL,
    request_path character varying(255) NOT NULL,
    request_method character varying(10) NOT NULL,
    request_payload text,
    request_ip character varying(50),
    login_location character varying(255),
    request_os character varying(64),
    request_browser character varying(64),
    response_code integer NOT NULL,
    response_json text,
    process_time character varying(20),
    creator_id integer,
    id integer NOT NULL,
    status boolean NOT NULL,
    description text,
    created_at timestamp without time zone NOT NULL,
    updated_at timestamp without time zone NOT NULL
);


ALTER TABLE public.system_log OWNER TO tao;

--
-- Name: TABLE system_log; Type: COMMENT; Schema: public; Owner: tao
--

COMMENT ON TABLE public.system_log IS '系统日志表';


--
-- Name: COLUMN system_log.type; Type: COMMENT; Schema: public; Owner: tao
--

COMMENT ON COLUMN public.system_log.type IS '日志类型(1登录日志 2操作日志)';


--
-- Name: COLUMN system_log.request_path; Type: COMMENT; Schema: public; Owner: tao
--

COMMENT ON COLUMN public.system_log.request_path IS '请求路径';


--
-- Name: COLUMN system_log.request_method; Type: COMMENT; Schema: public; Owner: tao
--

COMMENT ON COLUMN public.system_log.request_method IS '请求方式';


--
-- Name: COLUMN system_log.request_payload; Type: COMMENT; Schema: public; Owner: tao
--

COMMENT ON COLUMN public.system_log.request_payload IS '请求体';


--
-- Name: COLUMN system_log.request_ip; Type: COMMENT; Schema: public; Owner: tao
--

COMMENT ON COLUMN public.system_log.request_ip IS '请求IP地址';


--
-- Name: COLUMN system_log.login_location; Type: COMMENT; Schema: public; Owner: tao
--

COMMENT ON COLUMN public.system_log.login_location IS '登录位置';


--
-- Name: COLUMN system_log.request_os; Type: COMMENT; Schema: public; Owner: tao
--

COMMENT ON COLUMN public.system_log.request_os IS '操作系统';


--
-- Name: COLUMN system_log.request_browser; Type: COMMENT; Schema: public; Owner: tao
--

COMMENT ON COLUMN public.system_log.request_browser IS '浏览器';


--
-- Name: COLUMN system_log.response_code; Type: COMMENT; Schema: public; Owner: tao
--

COMMENT ON COLUMN public.system_log.response_code IS '响应状态码';


--
-- Name: COLUMN system_log.response_json; Type: COMMENT; Schema: public; Owner: tao
--

COMMENT ON COLUMN public.system_log.response_json IS '响应体';


--
-- Name: COLUMN system_log.process_time; Type: COMMENT; Schema: public; Owner: tao
--

COMMENT ON COLUMN public.system_log.process_time IS '处理时间';


--
-- Name: COLUMN system_log.creator_id; Type: COMMENT; Schema: public; Owner: tao
--

COMMENT ON COLUMN public.system_log.creator_id IS '创建人ID';


--
-- Name: COLUMN system_log.id; Type: COMMENT; Schema: public; Owner: tao
--

COMMENT ON COLUMN public.system_log.id IS '主键ID';


--
-- Name: COLUMN system_log.status; Type: COMMENT; Schema: public; Owner: tao
--

COMMENT ON COLUMN public.system_log.status IS '是否启用(True:启用 False:禁用)';


--
-- Name: COLUMN system_log.description; Type: COMMENT; Schema: public; Owner: tao
--

COMMENT ON COLUMN public.system_log.description IS '备注说明';


--
-- Name: COLUMN system_log.created_at; Type: COMMENT; Schema: public; Owner: tao
--

COMMENT ON COLUMN public.system_log.created_at IS '创建时间';


--
-- Name: COLUMN system_log.updated_at; Type: COMMENT; Schema: public; Owner: tao
--

COMMENT ON COLUMN public.system_log.updated_at IS '更新时间';


--
-- Name: system_log_id_seq; Type: SEQUENCE; Schema: public; Owner: tao
--

CREATE SEQUENCE public.system_log_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.system_log_id_seq OWNER TO tao;

--
-- Name: system_log_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: tao
--

ALTER SEQUENCE public.system_log_id_seq OWNED BY public.system_log.id;


--
-- Name: system_menu; Type: TABLE; Schema: public; Owner: tao
--

CREATE TABLE public.system_menu (
    name character varying(50) NOT NULL,
    type integer NOT NULL,
    "order" integer NOT NULL,
    permission character varying(100),
    icon character varying(50),
    route_name character varying(100),
    route_path character varying(200),
    component_path character varying(200),
    redirect character varying(200),
    hidden boolean NOT NULL,
    keep_alive boolean NOT NULL,
    always_show boolean NOT NULL,
    title character varying(50),
    params json,
    affix boolean NOT NULL,
    parent_id integer,
    id integer NOT NULL,
    status boolean NOT NULL,
    description text,
    created_at timestamp without time zone NOT NULL,
    updated_at timestamp without time zone NOT NULL
);


ALTER TABLE public.system_menu OWNER TO tao;

--
-- Name: TABLE system_menu; Type: COMMENT; Schema: public; Owner: tao
--

COMMENT ON TABLE public.system_menu IS '菜单表';


--
-- Name: COLUMN system_menu.name; Type: COMMENT; Schema: public; Owner: tao
--

COMMENT ON COLUMN public.system_menu.name IS '菜单名称';


--
-- Name: COLUMN system_menu.type; Type: COMMENT; Schema: public; Owner: tao
--

COMMENT ON COLUMN public.system_menu.type IS '菜单类型(1:目录 2:菜单 3:按钮/权限 4:链接)';


--
-- Name: COLUMN system_menu."order"; Type: COMMENT; Schema: public; Owner: tao
--

COMMENT ON COLUMN public.system_menu."order" IS '显示排序';


--
-- Name: COLUMN system_menu.permission; Type: COMMENT; Schema: public; Owner: tao
--

COMMENT ON COLUMN public.system_menu.permission IS '权限标识(如：system:user:list)';


--
-- Name: COLUMN system_menu.icon; Type: COMMENT; Schema: public; Owner: tao
--

COMMENT ON COLUMN public.system_menu.icon IS '菜单图标';


--
-- Name: COLUMN system_menu.route_name; Type: COMMENT; Schema: public; Owner: tao
--

COMMENT ON COLUMN public.system_menu.route_name IS '路由名称';


--
-- Name: COLUMN system_menu.route_path; Type: COMMENT; Schema: public; Owner: tao
--

COMMENT ON COLUMN public.system_menu.route_path IS '路由路径';


--
-- Name: COLUMN system_menu.component_path; Type: COMMENT; Schema: public; Owner: tao
--

COMMENT ON COLUMN public.system_menu.component_path IS '组件路径';


--
-- Name: COLUMN system_menu.redirect; Type: COMMENT; Schema: public; Owner: tao
--

COMMENT ON COLUMN public.system_menu.redirect IS '重定向地址';


--
-- Name: COLUMN system_menu.hidden; Type: COMMENT; Schema: public; Owner: tao
--

COMMENT ON COLUMN public.system_menu.hidden IS '是否隐藏(True:隐藏 False:显示)';


--
-- Name: COLUMN system_menu.keep_alive; Type: COMMENT; Schema: public; Owner: tao
--

COMMENT ON COLUMN public.system_menu.keep_alive IS '是否缓存(True:是 False:否)';


--
-- Name: COLUMN system_menu.always_show; Type: COMMENT; Schema: public; Owner: tao
--

COMMENT ON COLUMN public.system_menu.always_show IS '是否始终显示(True:是 False:否)';


--
-- Name: COLUMN system_menu.title; Type: COMMENT; Schema: public; Owner: tao
--

COMMENT ON COLUMN public.system_menu.title IS '菜单标题';


--
-- Name: COLUMN system_menu.params; Type: COMMENT; Schema: public; Owner: tao
--

COMMENT ON COLUMN public.system_menu.params IS '路由参数(JSON对象)';


--
-- Name: COLUMN system_menu.affix; Type: COMMENT; Schema: public; Owner: tao
--

COMMENT ON COLUMN public.system_menu.affix IS '是否固定标签页(True:是 False:否)';


--
-- Name: COLUMN system_menu.parent_id; Type: COMMENT; Schema: public; Owner: tao
--

COMMENT ON COLUMN public.system_menu.parent_id IS '父菜单ID';


--
-- Name: COLUMN system_menu.id; Type: COMMENT; Schema: public; Owner: tao
--

COMMENT ON COLUMN public.system_menu.id IS '主键ID';


--
-- Name: COLUMN system_menu.status; Type: COMMENT; Schema: public; Owner: tao
--

COMMENT ON COLUMN public.system_menu.status IS '是否启用(True:启用 False:禁用)';


--
-- Name: COLUMN system_menu.description; Type: COMMENT; Schema: public; Owner: tao
--

COMMENT ON COLUMN public.system_menu.description IS '备注说明';


--
-- Name: COLUMN system_menu.created_at; Type: COMMENT; Schema: public; Owner: tao
--

COMMENT ON COLUMN public.system_menu.created_at IS '创建时间';


--
-- Name: COLUMN system_menu.updated_at; Type: COMMENT; Schema: public; Owner: tao
--

COMMENT ON COLUMN public.system_menu.updated_at IS '更新时间';


--
-- Name: system_menu_id_seq; Type: SEQUENCE; Schema: public; Owner: tao
--

CREATE SEQUENCE public.system_menu_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.system_menu_id_seq OWNER TO tao;

--
-- Name: system_menu_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: tao
--

ALTER SEQUENCE public.system_menu_id_seq OWNED BY public.system_menu.id;


--
-- Name: system_notice; Type: TABLE; Schema: public; Owner: tao
--

CREATE TABLE public.system_notice (
    notice_title character varying(50) NOT NULL,
    notice_type character varying(50) NOT NULL,
    notice_content text,
    creator_id integer,
    id integer NOT NULL,
    status boolean NOT NULL,
    description text,
    created_at timestamp without time zone NOT NULL,
    updated_at timestamp without time zone NOT NULL
);


ALTER TABLE public.system_notice OWNER TO tao;

--
-- Name: TABLE system_notice; Type: COMMENT; Schema: public; Owner: tao
--

COMMENT ON TABLE public.system_notice IS '通知公告表';


--
-- Name: COLUMN system_notice.notice_title; Type: COMMENT; Schema: public; Owner: tao
--

COMMENT ON COLUMN public.system_notice.notice_title IS '公告标题';


--
-- Name: COLUMN system_notice.notice_type; Type: COMMENT; Schema: public; Owner: tao
--

COMMENT ON COLUMN public.system_notice.notice_type IS '公告类型（1通知 2公告）';


--
-- Name: COLUMN system_notice.notice_content; Type: COMMENT; Schema: public; Owner: tao
--

COMMENT ON COLUMN public.system_notice.notice_content IS '公告内容';


--
-- Name: COLUMN system_notice.creator_id; Type: COMMENT; Schema: public; Owner: tao
--

COMMENT ON COLUMN public.system_notice.creator_id IS '创建人ID';


--
-- Name: COLUMN system_notice.id; Type: COMMENT; Schema: public; Owner: tao
--

COMMENT ON COLUMN public.system_notice.id IS '主键ID';


--
-- Name: COLUMN system_notice.status; Type: COMMENT; Schema: public; Owner: tao
--

COMMENT ON COLUMN public.system_notice.status IS '是否启用(True:启用 False:禁用)';


--
-- Name: COLUMN system_notice.description; Type: COMMENT; Schema: public; Owner: tao
--

COMMENT ON COLUMN public.system_notice.description IS '备注说明';


--
-- Name: COLUMN system_notice.created_at; Type: COMMENT; Schema: public; Owner: tao
--

COMMENT ON COLUMN public.system_notice.created_at IS '创建时间';


--
-- Name: COLUMN system_notice.updated_at; Type: COMMENT; Schema: public; Owner: tao
--

COMMENT ON COLUMN public.system_notice.updated_at IS '更新时间';


--
-- Name: system_notice_id_seq; Type: SEQUENCE; Schema: public; Owner: tao
--

CREATE SEQUENCE public.system_notice_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.system_notice_id_seq OWNER TO tao;

--
-- Name: system_notice_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: tao
--

ALTER SEQUENCE public.system_notice_id_seq OWNED BY public.system_notice.id;


--
-- Name: system_position; Type: TABLE; Schema: public; Owner: tao
--

CREATE TABLE public.system_position (
    name character varying(40) NOT NULL,
    "order" integer NOT NULL,
    creator_id integer,
    id integer NOT NULL,
    status boolean NOT NULL,
    description text,
    created_at timestamp without time zone NOT NULL,
    updated_at timestamp without time zone NOT NULL
);


ALTER TABLE public.system_position OWNER TO tao;

--
-- Name: TABLE system_position; Type: COMMENT; Schema: public; Owner: tao
--

COMMENT ON TABLE public.system_position IS '岗位表';


--
-- Name: COLUMN system_position.name; Type: COMMENT; Schema: public; Owner: tao
--

COMMENT ON COLUMN public.system_position.name IS '岗位名称';


--
-- Name: COLUMN system_position."order"; Type: COMMENT; Schema: public; Owner: tao
--

COMMENT ON COLUMN public.system_position."order" IS '显示排序';


--
-- Name: COLUMN system_position.creator_id; Type: COMMENT; Schema: public; Owner: tao
--

COMMENT ON COLUMN public.system_position.creator_id IS '创建人ID';


--
-- Name: COLUMN system_position.id; Type: COMMENT; Schema: public; Owner: tao
--

COMMENT ON COLUMN public.system_position.id IS '主键ID';


--
-- Name: COLUMN system_position.status; Type: COMMENT; Schema: public; Owner: tao
--

COMMENT ON COLUMN public.system_position.status IS '是否启用(True:启用 False:禁用)';


--
-- Name: COLUMN system_position.description; Type: COMMENT; Schema: public; Owner: tao
--

COMMENT ON COLUMN public.system_position.description IS '备注说明';


--
-- Name: COLUMN system_position.created_at; Type: COMMENT; Schema: public; Owner: tao
--

COMMENT ON COLUMN public.system_position.created_at IS '创建时间';


--
-- Name: COLUMN system_position.updated_at; Type: COMMENT; Schema: public; Owner: tao
--

COMMENT ON COLUMN public.system_position.updated_at IS '更新时间';


--
-- Name: system_position_id_seq; Type: SEQUENCE; Schema: public; Owner: tao
--

CREATE SEQUENCE public.system_position_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.system_position_id_seq OWNER TO tao;

--
-- Name: system_position_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: tao
--

ALTER SEQUENCE public.system_position_id_seq OWNED BY public.system_position.id;


--
-- Name: system_role; Type: TABLE; Schema: public; Owner: tao
--

CREATE TABLE public.system_role (
    name character varying(40) NOT NULL,
    code character varying(20),
    "order" integer NOT NULL,
    data_scope integer NOT NULL,
    creator_id integer,
    id integer NOT NULL,
    status boolean NOT NULL,
    description text,
    created_at timestamp without time zone NOT NULL,
    updated_at timestamp without time zone NOT NULL
);


ALTER TABLE public.system_role OWNER TO tao;

--
-- Name: TABLE system_role; Type: COMMENT; Schema: public; Owner: tao
--

COMMENT ON TABLE public.system_role IS '角色表';


--
-- Name: COLUMN system_role.name; Type: COMMENT; Schema: public; Owner: tao
--

COMMENT ON COLUMN public.system_role.name IS '角色名称';


--
-- Name: COLUMN system_role.code; Type: COMMENT; Schema: public; Owner: tao
--

COMMENT ON COLUMN public.system_role.code IS '角色编码';


--
-- Name: COLUMN system_role."order"; Type: COMMENT; Schema: public; Owner: tao
--

COMMENT ON COLUMN public.system_role."order" IS '显示排序';


--
-- Name: COLUMN system_role.data_scope; Type: COMMENT; Schema: public; Owner: tao
--

COMMENT ON COLUMN public.system_role.data_scope IS '数据权限范围';


--
-- Name: COLUMN system_role.creator_id; Type: COMMENT; Schema: public; Owner: tao
--

COMMENT ON COLUMN public.system_role.creator_id IS '创建人ID';


--
-- Name: COLUMN system_role.id; Type: COMMENT; Schema: public; Owner: tao
--

COMMENT ON COLUMN public.system_role.id IS '主键ID';


--
-- Name: COLUMN system_role.status; Type: COMMENT; Schema: public; Owner: tao
--

COMMENT ON COLUMN public.system_role.status IS '是否启用(True:启用 False:禁用)';


--
-- Name: COLUMN system_role.description; Type: COMMENT; Schema: public; Owner: tao
--

COMMENT ON COLUMN public.system_role.description IS '备注说明';


--
-- Name: COLUMN system_role.created_at; Type: COMMENT; Schema: public; Owner: tao
--

COMMENT ON COLUMN public.system_role.created_at IS '创建时间';


--
-- Name: COLUMN system_role.updated_at; Type: COMMENT; Schema: public; Owner: tao
--

COMMENT ON COLUMN public.system_role.updated_at IS '更新时间';


--
-- Name: system_role_depts; Type: TABLE; Schema: public; Owner: tao
--

CREATE TABLE public.system_role_depts (
    role_id integer NOT NULL,
    dept_id integer NOT NULL
);


ALTER TABLE public.system_role_depts OWNER TO tao;

--
-- Name: TABLE system_role_depts; Type: COMMENT; Schema: public; Owner: tao
--

COMMENT ON TABLE public.system_role_depts IS '角色部门关联表';


--
-- Name: COLUMN system_role_depts.role_id; Type: COMMENT; Schema: public; Owner: tao
--

COMMENT ON COLUMN public.system_role_depts.role_id IS '角色ID';


--
-- Name: COLUMN system_role_depts.dept_id; Type: COMMENT; Schema: public; Owner: tao
--

COMMENT ON COLUMN public.system_role_depts.dept_id IS '部门ID';


--
-- Name: system_role_id_seq; Type: SEQUENCE; Schema: public; Owner: tao
--

CREATE SEQUENCE public.system_role_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.system_role_id_seq OWNER TO tao;

--
-- Name: system_role_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: tao
--

ALTER SEQUENCE public.system_role_id_seq OWNED BY public.system_role.id;


--
-- Name: system_role_menus; Type: TABLE; Schema: public; Owner: tao
--

CREATE TABLE public.system_role_menus (
    role_id integer NOT NULL,
    menu_id integer NOT NULL
);


ALTER TABLE public.system_role_menus OWNER TO tao;

--
-- Name: TABLE system_role_menus; Type: COMMENT; Schema: public; Owner: tao
--

COMMENT ON TABLE public.system_role_menus IS '角色菜单关联表';


--
-- Name: COLUMN system_role_menus.role_id; Type: COMMENT; Schema: public; Owner: tao
--

COMMENT ON COLUMN public.system_role_menus.role_id IS '角色ID';


--
-- Name: COLUMN system_role_menus.menu_id; Type: COMMENT; Schema: public; Owner: tao
--

COMMENT ON COLUMN public.system_role_menus.menu_id IS '菜单ID';


--
-- Name: system_user_positions; Type: TABLE; Schema: public; Owner: tao
--

CREATE TABLE public.system_user_positions (
    user_id integer NOT NULL,
    position_id integer NOT NULL
);


ALTER TABLE public.system_user_positions OWNER TO tao;

--
-- Name: TABLE system_user_positions; Type: COMMENT; Schema: public; Owner: tao
--

COMMENT ON TABLE public.system_user_positions IS '用户岗位关联表';


--
-- Name: COLUMN system_user_positions.user_id; Type: COMMENT; Schema: public; Owner: tao
--

COMMENT ON COLUMN public.system_user_positions.user_id IS '用户ID';


--
-- Name: COLUMN system_user_positions.position_id; Type: COMMENT; Schema: public; Owner: tao
--

COMMENT ON COLUMN public.system_user_positions.position_id IS '岗位ID';


--
-- Name: system_user_roles; Type: TABLE; Schema: public; Owner: tao
--

CREATE TABLE public.system_user_roles (
    user_id integer NOT NULL,
    role_id integer NOT NULL
);


ALTER TABLE public.system_user_roles OWNER TO tao;

--
-- Name: TABLE system_user_roles; Type: COMMENT; Schema: public; Owner: tao
--

COMMENT ON TABLE public.system_user_roles IS '用户角色关联表';


--
-- Name: COLUMN system_user_roles.user_id; Type: COMMENT; Schema: public; Owner: tao
--

COMMENT ON COLUMN public.system_user_roles.user_id IS '用户ID';


--
-- Name: COLUMN system_user_roles.role_id; Type: COMMENT; Schema: public; Owner: tao
--

COMMENT ON COLUMN public.system_user_roles.role_id IS '角色ID';


--
-- Name: system_users; Type: TABLE; Schema: public; Owner: tao
--

CREATE TABLE public.system_users (
    username character varying(32) NOT NULL,
    password character varying(255) NOT NULL,
    name character varying(32) NOT NULL,
    mobile character varying(20),
    email character varying(64),
    gender character varying(1),
    avatar character varying(500),
    is_superuser boolean NOT NULL,
    last_login timestamp with time zone,
    dept_id integer,
    creator_id integer,
    id integer NOT NULL,
    status boolean NOT NULL,
    description text,
    created_at timestamp without time zone NOT NULL,
    updated_at timestamp without time zone NOT NULL
);


ALTER TABLE public.system_users OWNER TO tao;

--
-- Name: TABLE system_users; Type: COMMENT; Schema: public; Owner: tao
--

COMMENT ON TABLE public.system_users IS '用户表';


--
-- Name: COLUMN system_users.username; Type: COMMENT; Schema: public; Owner: tao
--

COMMENT ON COLUMN public.system_users.username IS '用户名/登录账号';


--
-- Name: COLUMN system_users.password; Type: COMMENT; Schema: public; Owner: tao
--

COMMENT ON COLUMN public.system_users.password IS '密码哈希';


--
-- Name: COLUMN system_users.name; Type: COMMENT; Schema: public; Owner: tao
--

COMMENT ON COLUMN public.system_users.name IS '昵称';


--
-- Name: COLUMN system_users.mobile; Type: COMMENT; Schema: public; Owner: tao
--

COMMENT ON COLUMN public.system_users.mobile IS '手机号';


--
-- Name: COLUMN system_users.email; Type: COMMENT; Schema: public; Owner: tao
--

COMMENT ON COLUMN public.system_users.email IS '邮箱';


--
-- Name: COLUMN system_users.gender; Type: COMMENT; Schema: public; Owner: tao
--

COMMENT ON COLUMN public.system_users.gender IS '性别(0:男 1:女 2:未知)';


--
-- Name: COLUMN system_users.avatar; Type: COMMENT; Schema: public; Owner: tao
--

COMMENT ON COLUMN public.system_users.avatar IS '头像URL地址';


--
-- Name: COLUMN system_users.is_superuser; Type: COMMENT; Schema: public; Owner: tao
--

COMMENT ON COLUMN public.system_users.is_superuser IS '是否超管';


--
-- Name: COLUMN system_users.last_login; Type: COMMENT; Schema: public; Owner: tao
--

COMMENT ON COLUMN public.system_users.last_login IS '最后登录时间';


--
-- Name: COLUMN system_users.dept_id; Type: COMMENT; Schema: public; Owner: tao
--

COMMENT ON COLUMN public.system_users.dept_id IS '部门ID';


--
-- Name: COLUMN system_users.creator_id; Type: COMMENT; Schema: public; Owner: tao
--

COMMENT ON COLUMN public.system_users.creator_id IS '创建人ID';


--
-- Name: COLUMN system_users.id; Type: COMMENT; Schema: public; Owner: tao
--

COMMENT ON COLUMN public.system_users.id IS '主键ID';


--
-- Name: COLUMN system_users.status; Type: COMMENT; Schema: public; Owner: tao
--

COMMENT ON COLUMN public.system_users.status IS '是否启用(True:启用 False:禁用)';


--
-- Name: COLUMN system_users.description; Type: COMMENT; Schema: public; Owner: tao
--

COMMENT ON COLUMN public.system_users.description IS '备注说明';


--
-- Name: COLUMN system_users.created_at; Type: COMMENT; Schema: public; Owner: tao
--

COMMENT ON COLUMN public.system_users.created_at IS '创建时间';


--
-- Name: COLUMN system_users.updated_at; Type: COMMENT; Schema: public; Owner: tao
--

COMMENT ON COLUMN public.system_users.updated_at IS '更新时间';


--
-- Name: system_users_id_seq; Type: SEQUENCE; Schema: public; Owner: tao
--

CREATE SEQUENCE public.system_users_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.system_users_id_seq OWNER TO tao;

--
-- Name: system_users_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: tao
--

ALTER SEQUENCE public.system_users_id_seq OWNED BY public.system_users.id;


--
-- Name: application_myapp id; Type: DEFAULT; Schema: public; Owner: tao
--

ALTER TABLE ONLY public.application_myapp ALTER COLUMN id SET DEFAULT nextval('public.application_myapp_id_seq'::regclass);


--
-- Name: example_demo id; Type: DEFAULT; Schema: public; Owner: tao
--

ALTER TABLE ONLY public.example_demo ALTER COLUMN id SET DEFAULT nextval('public.example_demo_id_seq'::regclass);


--
-- Name: monitor_job id; Type: DEFAULT; Schema: public; Owner: tao
--

ALTER TABLE ONLY public.monitor_job ALTER COLUMN id SET DEFAULT nextval('public.monitor_job_id_seq'::regclass);


--
-- Name: monitor_job_log id; Type: DEFAULT; Schema: public; Owner: tao
--

ALTER TABLE ONLY public.monitor_job_log ALTER COLUMN id SET DEFAULT nextval('public.monitor_job_log_id_seq'::regclass);


--
-- Name: system_config id; Type: DEFAULT; Schema: public; Owner: tao
--

ALTER TABLE ONLY public.system_config ALTER COLUMN id SET DEFAULT nextval('public.system_config_id_seq'::regclass);


--
-- Name: system_dept id; Type: DEFAULT; Schema: public; Owner: tao
--

ALTER TABLE ONLY public.system_dept ALTER COLUMN id SET DEFAULT nextval('public.system_dept_id_seq'::regclass);


--
-- Name: system_dict_data id; Type: DEFAULT; Schema: public; Owner: tao
--

ALTER TABLE ONLY public.system_dict_data ALTER COLUMN id SET DEFAULT nextval('public.system_dict_data_id_seq'::regclass);


--
-- Name: system_dict_type id; Type: DEFAULT; Schema: public; Owner: tao
--

ALTER TABLE ONLY public.system_dict_type ALTER COLUMN id SET DEFAULT nextval('public.system_dict_type_id_seq'::regclass);


--
-- Name: system_log id; Type: DEFAULT; Schema: public; Owner: tao
--

ALTER TABLE ONLY public.system_log ALTER COLUMN id SET DEFAULT nextval('public.system_log_id_seq'::regclass);


--
-- Name: system_menu id; Type: DEFAULT; Schema: public; Owner: tao
--

ALTER TABLE ONLY public.system_menu ALTER COLUMN id SET DEFAULT nextval('public.system_menu_id_seq'::regclass);


--
-- Name: system_notice id; Type: DEFAULT; Schema: public; Owner: tao
--

ALTER TABLE ONLY public.system_notice ALTER COLUMN id SET DEFAULT nextval('public.system_notice_id_seq'::regclass);


--
-- Name: system_position id; Type: DEFAULT; Schema: public; Owner: tao
--

ALTER TABLE ONLY public.system_position ALTER COLUMN id SET DEFAULT nextval('public.system_position_id_seq'::regclass);


--
-- Name: system_role id; Type: DEFAULT; Schema: public; Owner: tao
--

ALTER TABLE ONLY public.system_role ALTER COLUMN id SET DEFAULT nextval('public.system_role_id_seq'::regclass);


--
-- Name: system_users id; Type: DEFAULT; Schema: public; Owner: tao
--

ALTER TABLE ONLY public.system_users ALTER COLUMN id SET DEFAULT nextval('public.system_users_id_seq'::regclass);


--
-- Data for Name: application_myapp; Type: TABLE DATA; Schema: public; Owner: tao
--

COPY public.application_myapp (name, access_url, icon_url, creator_id, id, status, description, created_at, updated_at) FROM stdin;
\.


--
-- Data for Name: example_demo; Type: TABLE DATA; Schema: public; Owner: tao
--

COPY public.example_demo (name, creator_id, id, status, description, created_at, updated_at) FROM stdin;
\.


--
-- Data for Name: monitor_job; Type: TABLE DATA; Schema: public; Owner: tao
--

COPY public.monitor_job (name, jobstore, executor, trigger, trigger_args, func, args, kwargs, "coalesce", max_instances, start_date, end_date, creator_id, id, status, description, created_at, updated_at) FROM stdin;
系统默认（无参）	default	default	cron	0 0 12 * * ?	scheduler_test.job	\N	\N	f	1	\N	\N	1	1	f	\N	2025-09-06 01:12:52.929482	2025-09-06 01:12:52.929483
系统默认（有参）	default	default	cron	0 0 12 * * ?	scheduler_test.job	test	\N	f	1	\N	\N	1	2	f	\N	2025-09-06 01:12:52.929484	2025-09-06 01:12:52.929484
系统默认（多参）	default	default	cron	0 0 12 * * ?	scheduler_test.job	new	{"test": 111}	f	1	\N	\N	1	3	f	\N	2025-09-06 01:12:52.929485	2025-09-06 01:12:52.929485
\.


--
-- Data for Name: monitor_job_log; Type: TABLE DATA; Schema: public; Owner: tao
--

COPY public.monitor_job_log (id, job_name, job_group, job_executor, invoke_target, job_args, job_kwargs, job_trigger, job_message, exception_info, job_id) FROM stdin;
\.


--
-- Data for Name: system_config; Type: TABLE DATA; Schema: public; Owner: tao
--

COPY public.system_config (config_name, config_key, config_value, config_type, creator_id, id, status, description, created_at, updated_at) FROM stdin;
网站名称	sys_web_title	FastAPI Vue3 Admin	t	1	1	t	网站名称	2025-09-06 01:12:52.92001	2025-09-06 01:12:52.920011
网站描述	sys_web_description	FastAPI Vue3 Admin 是完全开源的权限管理系统	t	1	2	t	网站描述	2025-09-06 01:12:52.920012	2025-09-06 01:12:52.920012
网页图标	sys_web_favicon	https://service.fastapiadmin.com/api/v1/static/image/favicon.png	t	1	3	t	网页图标	2025-09-06 01:12:52.920013	2025-09-06 01:12:52.920013
网站Logo	sys_web_logo	https://service.fastapiadmin.com/api/v1/static/image/logo.png	t	1	4	t	网站Logo	2025-09-06 01:12:52.920014	2025-09-06 01:12:52.920014
登录背景	sys_login_background	https://service.fastapiadmin.com/api/v1/static/image/background.svg	t	1	5	t	登录背景	2025-09-06 01:12:52.920014	2025-09-06 01:12:52.920015
版权信息	sys_web_copyright	Copyright © 2025-2026 service.fastapiadmin.com 版权所有	t	1	6	t	版权信息	2025-09-06 01:12:52.920015	2025-09-06 01:12:52.920016
备案信息	sys_keep_record	陕ICP备2025069493号-1	t	1	7	t	备案信息	2025-09-06 01:12:52.920016	2025-09-06 01:12:52.920016
帮助文档	sys_help_doc	https://service.fastapiadmin.com	t	1	8	t	帮助文档	2025-09-06 01:12:52.920017	2025-09-06 01:12:52.920017
隐私政策	sys_web_privacy	https://github.com/1014TaoTao/fastapi_vue3_admin/blob/master/LICENSE	t	1	9	t	隐私政策	2025-09-06 01:12:52.920018	2025-09-06 01:12:52.920018
用户协议	sys_web_clause	https://github.com/1014TaoTao/fastapi_vue3_admin/blob/master/LICENSE	t	1	10	t	用户协议	2025-09-06 01:12:52.920019	2025-09-06 01:12:52.920019
源码代码	sys_git_code	https://github.com/1014TaoTao/fastapi_vue3_admin.git	t	1	11	t	源码代码	2025-09-06 01:12:52.920019	2025-09-06 01:12:52.92002
项目版本	sys_web_version	2.0.0	t	1	12	t	项目版本	2025-09-06 01:12:52.92002	2025-09-06 01:12:52.920021
\.


--
-- Data for Name: system_dept; Type: TABLE DATA; Schema: public; Owner: tao
--

COPY public.system_dept (name, "order", parent_id, id, status, description, created_at, updated_at) FROM stdin;
集团总公司	1	\N	1	t	集团总公司	2025-09-06 01:12:52.901006	2025-09-06 01:12:52.901009
西安分公司	1	1	2	t	西安分公司	2025-09-06 01:12:52.90101	2025-09-06 01:12:52.90101
深圳分公司	2	1	3	t	深圳分公司	2025-09-06 01:12:52.90101	2025-09-06 01:12:52.901011
开发组	1	2	4	t	开发组	2025-09-06 01:12:52.901011	2025-09-06 01:12:52.901011
测试组	2	2	5	t	测试组	2025-09-06 01:12:52.901012	2025-09-06 01:12:52.901012
演示组	3	2	6	t	演示组	2025-09-06 01:12:52.901012	2025-09-06 01:12:52.901013
销售部	1	3	7	t	销售部	2025-09-06 01:12:52.901013	2025-09-06 01:12:52.901013
市场部	2	3	8	t	市场部	2025-09-06 01:12:52.901014	2025-09-06 01:12:52.901014
财务部	3	3	9	t	财务部	2025-09-06 01:12:52.901015	2025-09-06 01:12:52.901015
研发部	4	3	10	t	研发部	2025-09-06 01:12:52.901015	2025-09-06 01:12:52.901016
运维部	5	3	11	t	研发部	2025-09-06 01:12:52.901016	2025-09-06 01:12:52.901016
\.


--
-- Data for Name: system_dict_data; Type: TABLE DATA; Schema: public; Owner: tao
--

COPY public.system_dict_data (dict_sort, dict_label, dict_value, dict_type, css_class, list_class, is_default, dict_type_id, creator_id, id, status, description, created_at, updated_at) FROM stdin;
1	男	0	sys_user_sex	blue	\N	t	\N	1	1	t	性别男	2025-09-06 01:12:52.927183	2025-09-06 01:12:52.927184
2	女	1	sys_user_sex	pink	\N	f	\N	1	2	t	性别女	2025-09-06 01:12:52.927185	2025-09-06 01:12:52.927185
3	未知	2	sys_user_sex	red	\N	f	\N	1	3	t	性别未知	2025-09-06 01:12:52.927186	2025-09-06 01:12:52.927186
1	启用	1	sys_common_status		primary	f	\N	1	4	t	启用状态	2025-09-06 01:12:52.927187	2025-09-06 01:12:52.927187
2	停用	0	sys_common_status		danger	f	\N	1	5	t	停用状态	2025-09-06 01:12:52.927187	2025-09-06 01:12:52.927188
1	是	1	sys_yes_no		primary	t	\N	1	6	t	是	2025-09-06 01:12:52.927188	2025-09-06 01:12:52.927188
2	否	0	sys_yes_no		danger	f	\N	1	7	t	否	2025-09-06 01:12:52.927189	2025-09-06 01:12:52.927189
99	其他	0	sys_oper_type		info	f	\N	1	8	t	其他操作	2025-09-06 01:12:52.92719	2025-09-06 01:12:52.92719
1	新增	1	sys_oper_type		info	f	\N	1	9	t	新增操作	2025-09-06 01:12:52.92719	2025-09-06 01:12:52.927191
2	修改	2	sys_oper_type		info	f	\N	1	10	t	修改操作	2025-09-06 01:12:52.927191	2025-09-06 01:12:52.927191
3	删除	3	sys_oper_type		danger	f	\N	1	11	t	删除操作	2025-09-06 01:12:52.927192	2025-09-06 01:12:52.927192
4	分配权限	4	sys_oper_type		primary	f	\N	1	12	t	授权操作	2025-09-06 01:12:52.927192	2025-09-06 01:12:52.927193
5	导出	5	sys_oper_type		warning	f	\N	1	13	t	导出操作	2025-09-06 01:12:52.927193	2025-09-06 01:12:52.927193
6	导入	6	sys_oper_type		warning	f	\N	1	14	t	导入操作	2025-09-06 01:12:52.927194	2025-09-06 01:12:52.927194
7	强退	7	sys_oper_type		danger	f	\N	1	15	t	强退操作	2025-09-06 01:12:52.927195	2025-09-06 01:12:52.927195
8	生成代码	8	sys_oper_type		warning	f	\N	1	16	t	生成操作	2025-09-06 01:12:52.927195	2025-09-06 01:12:52.927196
9	清空数据	9	sys_oper_type		danger	f	\N	1	17	t	清空操作	2025-09-06 01:12:52.927196	2025-09-06 01:12:52.927196
1	通知	1	sys_notice_type	blue	warning	t	\N	1	18	t	通知	2025-09-06 01:12:52.927197	2025-09-06 01:12:52.927197
2	公告	2	sys_notice_type	orange	success	f	\N	1	19	t	公告	2025-09-06 01:12:52.927197	2025-09-06 01:12:52.927198
1	默认(Memory)	default	sys_job_store		\N	t	\N	1	20	t	默认分组	2025-09-06 01:12:52.927198	2025-09-06 01:12:52.927198
2	数据库(Sqlalchemy)	sqlalchemy	sys_job_store		\N	f	\N	1	21	t	数据库分组	2025-09-06 01:12:52.927199	2025-09-06 01:12:52.927199
3	数据库(Redis)	redis	sys_job_store		\N	f	\N	1	22	t	reids分组	2025-09-06 01:12:52.927199	2025-09-06 01:12:52.9272
1	线程池	default	sys_job_executor		\N	f	\N	1	23	t	线程池	2025-09-06 01:12:52.9272	2025-09-06 01:12:52.927201
2	进程池	processpool	sys_job_executor		\N	f	\N	1	24	t	进程池	2025-09-06 01:12:52.927201	2025-09-06 01:12:52.927201
1	演示函数	scheduler_test.job	sys_job_function		\N	t	\N	1	25	t	演示函数	2025-09-06 01:12:52.927202	2025-09-06 01:12:52.927202
1	指定日期(date)	date	sys_job_trigger		\N	t	\N	1	26	t	指定日期任务触发器	2025-09-06 01:12:52.927202	2025-09-06 01:12:52.927203
2	间隔触发器(interval)	interval	sys_job_trigger		\N	f	\N	1	27	t	间隔触发器任务触发器	2025-09-06 01:12:52.927203	2025-09-06 01:12:52.927203
3	cron表达式	cron	sys_job_trigger		\N	f	\N	1	28	t	间隔触发器任务触发器	2025-09-06 01:12:52.927204	2025-09-06 01:12:52.927204
1	默认(default)	default	sys_list_class		\N	t	\N	1	29	t	默认表格回显样式	2025-09-06 01:12:52.927204	2025-09-06 01:12:52.927205
2	主要(primary)	primary	sys_list_class		\N	f	\N	1	30	t	主要表格回显样式	2025-09-06 01:12:52.927205	2025-09-06 01:12:52.927205
3	成功(success)	success	sys_list_class		\N	f	\N	1	31	t	成功表格回显样式	2025-09-06 01:12:52.927206	2025-09-06 01:12:52.927206
4	信息(info)	info	sys_list_class		\N	f	\N	1	32	t	信息表格回显样式	2025-09-06 01:12:52.927206	2025-09-06 01:12:52.927207
5	警告(warning)	warning	sys_list_class		\N	f	\N	1	33	t	警告表格回显样式	2025-09-06 01:12:52.927207	2025-09-06 01:12:52.927207
6	危险(danger)	danger	sys_list_class		\N	f	\N	1	34	t	危险表格回显样式	2025-09-06 01:12:52.927208	2025-09-06 01:12:52.927208
\.


--
-- Data for Name: system_dict_type; Type: TABLE DATA; Schema: public; Owner: tao
--

COPY public.system_dict_type (dict_name, dict_type, creator_id, id, status, description, created_at, updated_at) FROM stdin;
用户性别	sys_user_sex	1	1	t	用户性别列表	2025-09-06 01:12:52.921936	2025-09-06 01:12:52.921937
系统是否	sys_yes_no	1	2	t	系统是否列表	2025-09-06 01:12:52.921937	2025-09-06 01:12:52.921937
系统状态	sys_common_status	1	3	t	系统状态	2025-09-06 01:12:52.921938	2025-09-06 01:12:52.921938
通知类型	sys_notice_type	1	4	t	通知类型列表	2025-09-06 01:12:52.921939	2025-09-06 01:12:52.921939
操作类型	sys_oper_type	1	5	t	操作类型列表	2025-09-06 01:12:52.921939	2025-09-06 01:12:52.92194
任务存储器	sys_job_store	1	6	t	任务分组列表	2025-09-06 01:12:52.92194	2025-09-06 01:12:52.92194
任务执行器	sys_job_executor	1	7	t	任务执行器列表	2025-09-06 01:12:52.921941	2025-09-06 01:12:52.921941
任务函数	sys_job_function	1	8	t	任务函数列表	2025-09-06 01:12:52.921941	2025-09-06 01:12:52.921942
任务触发器	sys_job_trigger	1	9	t	任务触发器列表	2025-09-06 01:12:52.921942	2025-09-06 01:12:52.921942
表格回显样式	sys_list_class	1	10	t	表格回显样式列表	2025-09-06 01:12:52.921943	2025-09-06 01:12:52.921943
\.


--
-- Data for Name: system_log; Type: TABLE DATA; Schema: public; Owner: tao
--

COPY public.system_log (type, request_path, request_method, request_payload, request_ip, login_location, request_os, request_browser, response_code, response_json, process_time, creator_id, id, status, description, created_at, updated_at) FROM stdin;
\.


--
-- Data for Name: system_menu; Type: TABLE DATA; Schema: public; Owner: tao
--

COPY public.system_menu (name, type, "order", permission, icon, route_name, route_path, component_path, redirect, hidden, keep_alive, always_show, title, params, affix, parent_id, id, status, description, created_at, updated_at) FROM stdin;
仪表盘	1	1		client	Dashboard	/dashboard	\N	/dashboard/workplace	f	t	t	仪表盘	null	f	\N	1	t	初始化数据	2025-09-06 01:12:52.908967	2025-09-06 01:12:52.908969
工作台	2	1	dashboard:workplace:query	homepage	Workplace	/dashboard/workplace	dashboard/workplace	\N	f	t	f	工作台	null	t	1	2	t	初始化数据	2025-09-06 01:12:52.908969	2025-09-06 01:12:52.90897
分析页	2	2	dashboard:analysis:query	el-icon-PieChart	Analysis	/dashboard/analysis	dashboard/analysis	\N	f	t	f	分析页	null	f	1	3	t	初始化数据	2025-09-06 01:12:52.90897	2025-09-06 01:12:52.908971
系统管理	1	2	\N	system	System	/system	\N	/system/menu	f	t	f	系统管理	null	f	\N	4	t	初始化数据	2025-09-06 01:12:52.908971	2025-09-06 01:12:52.908971
菜单管理	2	1	system:menu:query	menu	Menu	/system/menu	system/menu/index	\N	f	t	f	菜单管理	null	f	4	5	t	初始化数据	2025-09-06 01:12:52.908972	2025-09-06 01:12:52.908972
部门管理	2	2	system:dept:query	tree	Dept	/system/dept	system/dept/index	\N	f	t	f	部门管理	null	f	4	6	t	初始化数据	2025-09-06 01:12:52.908972	2025-09-06 01:12:52.908973
岗位管理	2	3	system:position:query	el-icon-Coordinate	Position	/system/position	system/position/index	\N	f	t	f	岗位管理	null	f	4	7	t	初始化数据	2025-09-06 01:12:52.908973	2025-09-06 01:12:52.908974
角色管理	2	4	system:role:query	role	Role	/system/role	system/role/index	\N	f	t	f	角色管理	null	f	4	8	t	初始化数据	2025-09-06 01:12:52.908974	2025-09-06 01:12:52.908974
用户管理	2	5	system:user:query	el-icon-User	User	/system/user	system/user/index	\N	f	t	f	用户管理	null	f	4	9	t	初始化数据	2025-09-06 01:12:52.908975	2025-09-06 01:12:52.908975
日志管理	2	6	system:log:query	el-icon-Aim	Log	/system/log	system/log/index	\N	f	t	f	日志管理	null	f	4	10	t	初始化数据	2025-09-06 01:12:52.908975	2025-09-06 01:12:52.908976
公告管理	2	7	system:notice:query	bell	Notice	/system/notice	system/notice/index	\N	f	t	f	公告管理	null	f	4	11	t	初始化数据	2025-09-06 01:12:52.908976	2025-09-06 01:12:52.908977
配置管理	2	8	system:config:query	setting	Config	/system/config	system/config/index	\N	f	t	f	配置管理	null	f	4	12	t	初始化数据	2025-09-06 01:12:52.908977	2025-09-06 01:12:52.908977
字典管理	2	9	system:dict_type:query	dict	Dict	/system/dict	system/dict/index	\N	f	t	f	字典管理	null	f	4	13	t	初始化数据	2025-09-06 01:12:52.908978	2025-09-06 01:12:52.908978
创建菜单	3	1	system:menu:create	\N	\N	\N	\N	\N	f	t	f	创建菜单	null	f	5	14	t	初始化数据	2025-09-06 01:12:52.908978	2025-09-06 01:12:52.908979
修改菜单	3	2	system:menu:update	\N	\N	\N	\N	\N	f	t	f	修改菜单	null	f	5	15	t	初始化数据	2025-09-06 01:12:52.908979	2025-09-06 01:12:52.90898
删除菜单	3	3	system:menu:delete	\N	\N	\N	\N	\N	f	t	f	删除菜单	null	f	5	16	t	初始化数据	2025-09-06 01:12:52.90898	2025-09-06 01:12:52.90898
批量修改菜单状态	3	4	system:menu:patch	\N	\N	\N	\N	\N	f	t	f	批量修改菜单状态	null	f	5	17	t	初始化数据	2025-09-06 01:12:52.908981	2025-09-06 01:12:52.908981
创建部门	3	1	system:dept:create	\N	\N	\N	\N	\N	f	t	f	创建部门	null	f	6	18	t	初始化数据	2025-09-06 01:12:52.908981	2025-09-06 01:12:52.908982
修改部门	3	2	system:dept:update	\N	\N	\N	\N	\N	f	t	f	修改部门	null	f	6	19	t	初始化数据	2025-09-06 01:12:52.908982	2025-09-06 01:12:52.908982
删除部门	3	3	system:dept:delete	\N	\N	\N	\N	\N	f	t	f	删除部门	null	f	6	20	t	初始化数据	2025-09-06 01:12:52.908983	2025-09-06 01:12:52.908983
批量修改部门状态	3	4	system:dept:patch	\N	\N	\N	\N	\N	f	t	f	批量修改部门状态	null	f	6	21	t	初始化数据	2025-09-06 01:12:52.908984	2025-09-06 01:12:52.908984
创建岗位	3	1	system:position:create	\N	\N	\N	\N	\N	f	t	f	创建岗位	null	f	7	22	t	初始化数据	2025-09-06 01:12:52.908984	2025-09-06 01:12:52.908985
修改岗位	3	2	system:position:update	\N	\N	\N	\N	\N	f	t	f	修改岗位	null	f	7	23	t	初始化数据	2025-09-06 01:12:52.908985	2025-09-06 01:12:52.908985
删除岗位	3	3	system:position:delete	\N	\N	\N	\N	\N	f	t	f	修改岗位	null	f	7	24	t	初始化数据	2025-09-06 01:12:52.908986	2025-09-06 01:12:52.908986
批量修改岗位状态	3	4	system:position:patch	\N	\N	\N	\N	\N	f	t	f	批量修改岗位状态	null	f	7	25	t	初始化数据	2025-09-06 01:12:52.908986	2025-09-06 01:12:52.908987
岗位导出	3	5	system:position:export	\N	\N	\N	\N	\N	f	t	f	岗位导出	null	f	7	26	t	初始化数据	2025-09-06 01:12:52.908987	2025-09-06 01:12:52.908988
创建角色	3	1	system:role:create	\N	\N	\N	\N	\N	f	t	f	创建角色	null	f	8	27	t	初始化数据	2025-09-06 01:12:52.908988	2025-09-06 01:12:52.908988
修改角色	3	2	system:role:update	\N	\N	\N	\N	\N	f	t	f	修改角色	null	f	8	28	t	初始化数据	2025-09-06 01:12:52.908989	2025-09-06 01:12:52.908989
删除角色	3	3	system:role:delete	\N	\N	\N	\N	\N	f	t	f	删除角色	null	f	8	29	t	初始化数据	2025-09-06 01:12:52.90899	2025-09-06 01:12:52.90899
批量修改角色状态	3	4	system:role:patch	\N	\N	\N	\N	\N	f	t	f	批量修改角色状态	null	f	8	30	t	初始化数据	2025-09-06 01:12:52.90899	2025-09-06 01:12:52.908991
设置角色权限	3	8	system:role:permission	\N	\N	\N	\N	\N	f	t	f	设置角色权限	null	f	7	31	t	初始化数据	2025-09-06 01:12:52.908991	2025-09-06 01:12:52.908992
角色导出	3	6	system:role:export	\N	\N	\N	\N	\N	f	t	f	角色导出	null	f	8	32	t	初始化数据	2025-09-06 01:12:52.908992	2025-09-06 01:12:52.908992
创建用户	3	1	system:user:create	\N	\N	\N	\N	\N	f	t	f	创建用户	null	f	9	33	t	初始化数据	2025-09-06 01:12:52.908993	2025-09-06 01:12:52.908994
修改用户	3	2	system:user:update	\N	\N	\N	\N	\N	f	t	f	修改用户	null	f	9	34	t	初始化数据	2025-09-06 01:12:52.908994	2025-09-06 01:12:52.908995
删除用户	3	3	system:user:delete	\N	\N	\N	\N	\N	f	t	f	删除用户	null	f	9	35	t	初始化数据	2025-09-06 01:12:52.908995	2025-09-06 01:12:52.908995
批量修改用户状态	3	4	system:user:patch	\N	\N	\N	\N	\N	f	t	f	批量修改用户状态	null	f	9	36	t	初始化数据	2025-09-06 01:12:52.908996	2025-09-06 01:12:52.908996
导出用户	3	5	system:user:export	\N	\N	\N	\N	\N	f	t	f	导出用户	null	f	9	37	t	初始化数据	2025-09-06 01:12:52.908997	2025-09-06 01:12:52.908997
导入用户	3	6	system:user:import	\N	\N	\N	\N	\N	f	t	f	导入用户	null	f	9	38	t	初始化数据	2025-09-06 01:12:52.908997	2025-09-06 01:12:52.908998
日志删除	3	1	system:operation_log:delete	\N	\N	\N	\N	\N	f	t	f	日志删除	null	f	10	39	t	初始化数据	2025-09-06 01:12:52.908998	2025-09-06 01:12:52.908999
日志导出	3	2	system:operation_log:export	\N	\N	\N	\N	\N	f	t	f	日志导出	null	f	10	40	t	初始化数据	2025-09-06 01:12:52.908999	2025-09-06 01:12:52.908999
公告创建	3	1	system:notice:create	\N	\N	\N	\N	\N	f	t	f	公告创建	null	f	11	41	t	初始化数据	2025-09-06 01:12:52.909	2025-09-06 01:12:52.909
公告修改	3	2	system:notice:update	\N	\N	\N	\N	\N	f	t	f	修改用户	null	f	11	42	t	初始化数据	2025-09-06 01:12:52.909	2025-09-06 01:12:52.909001
公告删除	3	3	system:notice:delete	\N	\N	\N	\N	\N	f	t	f	公告删除	null	f	11	43	t	初始化数据	2025-09-06 01:12:52.909001	2025-09-06 01:12:52.909001
公告导出	3	4	system:notice:export	\N	\N	\N	\N	\N	f	t	f	公告导出	null	f	11	44	t	初始化数据	2025-09-06 01:12:52.909002	2025-09-06 01:12:52.909002
公告批量修改状态	3	5	system:notice:patch	\N	\N	\N	\N	\N	f	t	f	公告批量修改状态	null	f	11	45	t	初始化数据	2025-09-06 01:12:52.909003	2025-09-06 01:12:52.909003
创建配置	3	1	system:config:create	\N	\N	\N	\N	\N	f	t	f	创建配置	null	f	12	46	t	初始化数据	2025-09-06 01:12:52.909003	2025-09-06 01:12:52.909004
修改配置	3	2	system:config:update	\N	\N	\N	\N	\N	f	t	f	修改配置	null	f	12	47	t	初始化数据	2025-09-06 01:12:52.909004	2025-09-06 01:12:52.909004
删除配置	3	3	system:config:delete	\N	\N	\N	\N	\N	f	t	f	删除配置	null	f	12	48	t	初始化数据	2025-09-06 01:12:52.909005	2025-09-06 01:12:52.909005
导出配置	3	4	system:config:export	\N	\N	\N	\N	\N	f	t	f	导出配置	null	f	12	49	t	初始化数据	2025-09-06 01:12:52.909006	2025-09-06 01:12:52.909006
配置上传	3	5	system:config:upload	\N	\N	\N	\N	\N	f	t	f	配置上传	null	f	12	50	t	初始化数据	2025-09-06 01:12:52.909006	2025-09-06 01:12:52.909007
创建字典类型	3	1	system:dict_type:create	\N	\N	\N	\N	\N	f	t	f	创建字典类型	null	f	13	51	t	初始化数据	2025-09-06 01:12:52.909007	2025-09-06 01:12:52.909007
修改字典类型	3	2	system:dict_type:update	\N	\N	\N	\N	\N	f	t	f	修改字典类型	null	f	13	52	t	初始化数据	2025-09-06 01:12:52.909008	2025-09-06 01:12:52.909008
删除字典类型	3	3	system:dict_type:delete	\N	\N	\N	\N	\N	f	t	f	删除字典类型	null	f	13	53	t	初始化数据	2025-09-06 01:12:52.909009	2025-09-06 01:12:52.909009
导出字典类型	3	4	system:dict_type:export	\N	\N	\N	\N	\N	f	t	f	导出字典类型	null	f	13	54	t	初始化数据	2025-09-06 01:12:52.909009	2025-09-06 01:12:52.90901
批量修改字典状态	3	5	system:dict_type:patch	\N	\N	\N	\N	\N	f	t	f	导出字典类型	null	f	13	55	t	初始化数据	2025-09-06 01:12:52.90901	2025-09-06 01:12:52.90901
字典数据查询	3	6	system:dict_data:query	\N	\N	\N	\N	\N	f	t	f	字典数据查询	null	f	13	56	t	初始化数据	2025-09-06 01:12:52.909011	2025-09-06 01:12:52.909011
创建字典数据	3	7	system:dict_data:create	\N	\N	\N	\N	\N	f	t	f	创建字典数据	null	f	13	57	t	初始化数据	2025-09-06 01:12:52.909011	2025-09-06 01:12:52.909012
修改字典数据	3	8	system:dict_data:update	\N	\N	\N	\N	\N	f	t	f	修改字典数据	null	f	13	58	t	初始化数据	2025-09-06 01:12:52.909012	2025-09-06 01:12:52.909013
删除字典数据	3	9	system:dict_data:delete	\N	\N	\N	\N	\N	f	t	f	删除字典数据	null	f	13	59	t	初始化数据	2025-09-06 01:12:52.909013	2025-09-06 01:12:52.909013
导出字典数据	3	10	system:dict_data:export	\N	\N	\N	\N	\N	f	t	f	导出字典数据	null	f	13	60	t	初始化数据	2025-09-06 01:12:52.909014	2025-09-06 01:12:52.909014
批量修改字典数据状态	3	11	system:dict_data:patch	\N	\N	\N	\N	\N	f	t	f	批量修改字典数据状态	null	f	13	61	t	初始化数据	2025-09-06 01:12:52.909014	2025-09-06 01:12:52.909015
监控管理	1	3	\N	monitor	Monitor	/monitor	\N	/monitor/online	f	f	f	监控管理	null	f	\N	62	t	初始化数据	2025-09-06 01:12:52.909015	2025-09-06 01:12:52.909016
任务管理	2	1	monitor:job:query	el-icon-DataLine	Job	/monitor/job	monitor/job/index	\N	f	t	f	任务管理	null	f	62	63	t	初始化数据	2025-09-06 01:12:52.909016	2025-09-06 01:12:52.909016
创建任务	3	1	monitor:job:create	\N	\N	\N	\N	\N	f	t	f	创建任务	null	f	63	64	t	初始化数据	2025-09-06 01:12:52.909017	2025-09-06 01:12:52.909017
修改和操作任务	3	2	monitor:job:update	\N	\N	\N	\N	\N	f	t	f	修改和操作任务	null	f	63	65	t	初始化数据	2025-09-06 01:12:52.909017	2025-09-06 01:12:52.909018
删除和清除任务	3	3	monitor:job:delete	\N	\N	\N	\N	\N	f	t	f	删除和清除任务	null	f	63	66	t	初始化数据	2025-09-06 01:12:52.909018	2025-09-06 01:12:52.909018
导出定时任务	3	4	monitor:job:export	\N	\N	\N	\N	\N	f	t	f	导出定时任务	null	f	63	67	t	初始化数据	2025-09-06 01:12:52.909019	2025-09-06 01:12:52.909019
在线用户	2	2	monitor:online:query	el-icon-Headset	MonitorOnline	/monitor/online	monitor/online/index	\N	f	f	f	在线用户	null	f	62	68	t	初始化数据	2025-09-06 01:12:52.90902	2025-09-06 01:12:52.90902
在线用户强制下线	3	1	monitor:online:delete	\N	\N	\N	\N	\N	f	f	f	在线用户强制下线	null	f	68	69	t	初始化数据	2025-09-06 01:12:52.90902	2025-09-06 01:12:52.909021
服务器监控	2	3	monitor:server:query	el-icon-Odometer	MonitorServer	/monitor/server	monitor/server/index	\N	f	f	f	服务器监控	null	f	62	70	t	初始化数据	2025-09-06 01:12:52.909021	2025-09-06 01:12:52.909021
缓存监控	2	4	monitor:cache:query	el-icon-Stopwatch	MonitorCache	/monitor/cache	monitor/cache/index	\N	f	f	f	缓存监控	null	f	62	71	t	初始化数据	2025-09-06 01:12:52.909022	2025-09-06 01:12:52.909022
清除缓存	3	1	monitor:cache:delete	\N	\N	\N	\N	\N	f	f	f	清除缓存	null	f	71	72	t	初始化数据	2025-09-06 01:12:52.909022	2025-09-06 01:12:52.909023
公共模块	1	4	\N	document	Common	/common	\N	/common/docs	f	f	f	公共模块	null	f	\N	73	t	初始化数据	2025-09-06 01:12:52.909023	2025-09-06 01:12:52.909023
接口管理	4	1	common:docs:query	api	Docs	/common/docs	common/docs/index	\N	f	f	f	接口管理	null	f	73	74	t	初始化数据	2025-09-06 01:12:52.909024	2025-09-06 01:12:52.909024
文档管理	4	2	common:redoc:query	el-icon-Document	Redoc	/common/redoc	common/redoc/index	\N	f	f	f	文档管理	null	f	73	75	t	初始化数据	2025-09-06 01:12:52.909025	2025-09-06 01:12:52.909025
演示模块	1	5	\N	el-icon-Document	Demo	/demo	\N	/demo/example	f	f	f	演示模块	null	f	\N	76	t	初始化数据	2025-09-06 01:12:52.909025	2025-09-06 01:12:52.909026
示例管理	2	1	demo:example:query	el-icon-DataLine	Example	/demo/example	demo/example/index	\N	f	t	f	示例管理	null	f	76	77	t	初始化数据	2025-09-06 01:12:52.909026	2025-09-06 01:12:52.909026
创建示例	3	1	demo:example:create	\N	\N	\N	\N	\N	f	t	f	创建示例	null	f	77	78	t	初始化数据	2025-09-06 01:12:52.909027	2025-09-06 01:12:52.909027
更新示例	3	2	demo:example:update	\N	\N	\N	\N	\N	f	t	f	更新示例	null	f	77	79	t	初始化数据	2025-09-06 01:12:52.909027	2025-09-06 01:12:52.909028
删除示例	3	3	demo:example:delete	\N	\N	\N	\N	\N	f	t	f	删除示例	null	f	77	80	t	初始化数据	2025-09-06 01:12:52.909028	2025-09-06 01:12:52.909029
批量修改示例状态	3	4	demo:example:patch	\N	\N	\N	\N	\N	f	t	f	批量修改示例状态	null	f	77	81	t	初始化数据	2025-09-06 01:12:52.909029	2025-09-06 01:12:52.909029
导出示例	3	5	demo:example:export	\N	\N	\N	\N	\N	f	t	f	导出示例	null	f	77	82	t	初始化数据	2025-09-06 01:12:52.90903	2025-09-06 01:12:52.90903
导入示例	3	6	demo:example:import	\N	\N	\N	\N	\N	f	t	f	导入示例	null	f	77	83	t	初始化数据	2025-09-06 01:12:52.90903	2025-09-06 01:12:52.909031
下载导入示例模版	3	7	demo:example:download	\N	\N	\N	\N	\N	f	t	f	下载导入示例模版	null	f	77	84	t	初始化数据	2025-09-06 01:12:52.909031	2025-09-06 01:12:52.909031
应用管理	1	6	\N	captcha	Application	/application	\N	/application/myapp	f	f	f	应用管理	null	f	\N	85	t	初始化数据	2025-09-06 01:12:52.909032	2025-09-06 01:12:52.909032
我的应用	2	1	application:myapp:query	el-icon-DataLine	ApplicationSystem	/application/myapp	application/myapp/index	\N	f	t	f	应用系统管理	null	f	85	86	t	初始化数据	2025-09-06 01:12:52.909033	2025-09-06 01:12:52.909033
创建应用	3	1	application:myapp:create	\N	\N	\N	\N	\N	f	t	f	创建应用	null	f	86	87	t	初始化数据	2025-09-06 01:12:52.909033	2025-09-06 01:12:52.909034
修改应用	3	2	application:myapp:update	\N	\N	\N	\N	\N	f	t	f	修改应用	null	f	86	88	t	初始化数据	2025-09-06 01:12:52.909034	2025-09-06 01:12:52.909034
删除应用	3	3	application:myapp:delete	\N	\N	\N	\N	\N	f	t	f	删除应用	null	f	86	89	t	初始化数据	2025-09-06 01:12:52.909035	2025-09-06 01:12:52.909035
批量修改应用状态	3	4	application:myapp:patch	\N	\N	\N	\N	\N	f	t	f	批量修改应用状态	null	f	86	90	t	初始化数据	2025-09-06 01:12:52.909036	2025-09-06 01:12:52.909036
资源管理	1	7	\N	document	Resource	/resource	\N	/resource/file	f	f	f	资源管理	null	f	\N	91	t	初始化数据	2025-09-06 01:12:52.909036	2025-09-06 01:12:52.909037
文件管理	2	1	resource:file:query	el-icon-Files	ResourceFile	/resource/file	resource/file/index	\N	f	t	f	文件管理	null	f	91	92	t	初始化数据	2025-09-06 01:12:52.909037	2025-09-06 01:12:52.909037
文件上传	3	1	resource:file:upload	\N	\N	\N	\N	\N	f	t	f	文件上传	null	f	92	93	t	初始化数据	2025-09-06 01:12:52.909038	2025-09-06 01:12:52.909038
文件下载	3	2	resource:file:download	\N	\N	\N	\N	\N	f	t	f	文件下载	null	f	92	94	t	初始化数据	2025-09-06 01:12:52.909038	2025-09-06 01:12:52.909039
文件删除	3	3	resource:file:delete	\N	\N	\N	\N	\N	f	t	f	文件删除	null	f	92	95	t	初始化数据	2025-09-06 01:12:52.909039	2025-09-06 01:12:52.909039
文件移动	3	4	resource:file:move	\N	\N	\N	\N	\N	f	t	f	文件移动	null	f	92	96	t	初始化数据	2025-09-06 01:12:52.90904	2025-09-06 01:12:52.90904
文件复制	3	5	resource:file:copy	\N	\N	\N	\N	\N	f	t	f	文件复制	null	f	92	97	t	初始化数据	2025-09-06 01:12:52.909041	2025-09-06 01:12:52.909041
文件重命名	3	6	resource:file:rename	\N	\N	\N	\N	\N	f	t	f	文件重命名	null	f	92	98	t	初始化数据	2025-09-06 01:12:52.909041	2025-09-06 01:12:52.909042
创建目录	3	7	resource:file:create_dir	\N	\N	\N	\N	\N	f	t	f	创建目录	null	f	92	99	t	初始化数据	2025-09-06 01:12:52.909042	2025-09-06 01:12:52.909042
文件搜索	3	8	resource:file:search	\N	\N	\N	\N	\N	f	t	f	文件搜索	null	f	92	100	t	初始化数据	2025-09-06 01:12:52.909043	2025-09-06 01:12:52.909043
导出文件列表	3	9	resource:file:export	\N	\N	\N	\N	\N	f	t	f	导出文件列表	null	f	92	101	t	初始化数据	2025-09-06 01:12:52.909043	2025-09-06 01:12:52.909044
\.


--
-- Data for Name: system_notice; Type: TABLE DATA; Schema: public; Owner: tao
--

COPY public.system_notice (notice_title, notice_type, notice_content, creator_id, id, status, description, created_at, updated_at) FROM stdin;
系统更新	1	2099年9月9日，晚上12:00，系统更新	1	1	t	系统更新	2025-09-06 01:12:52.923567	2025-09-06 01:12:52.923568
系统维护	2	2099年9月9日，晚上12:00，系统维护	1	2	t	系统维护	2025-09-06 01:12:52.923569	2025-09-06 01:12:52.923569
系统更新完成	1	2099年9月9日，晚上12:00，系统更新完成	1	3	f	系统更新完成	2025-09-06 01:12:52.92357	2025-09-06 01:12:52.92357
系统维护完成	2	2099年9月9日，晚上12:00，系统维护完成	1	4	f	系统维护完成	2025-09-06 01:12:52.92357	2025-09-06 01:12:52.923571
\.


--
-- Data for Name: system_position; Type: TABLE DATA; Schema: public; Owner: tao
--

COPY public.system_position (name, "order", creator_id, id, status, description, created_at, updated_at) FROM stdin;
董事长岗	1	1	1	t	董事长岗位	2025-09-06 01:12:52.917888	2025-09-06 01:12:52.917889
运营岗	2	1	2	t	运营岗位	2025-09-06 01:12:52.917889	2025-09-06 01:12:52.91789
销售岗	3	1	3	t	销售岗	2025-09-06 01:12:52.91789	2025-09-06 01:12:52.91789
人事行政岗	4	1	4	t	人事行政岗	2025-09-06 01:12:52.917891	2025-09-06 01:12:52.917891
开发岗	5	1	5	t	开发岗	2025-09-06 01:12:52.917892	2025-09-06 01:12:52.917892
测试岗	6	1	6	t	测试岗	2025-09-06 01:12:52.917892	2025-09-06 01:12:52.917893
演示岗	7	1	7	t	演示岗	2025-09-06 01:12:52.917893	2025-09-06 01:12:52.917893
\.


--
-- Data for Name: system_role; Type: TABLE DATA; Schema: public; Owner: tao
--

COPY public.system_role (name, code, "order", data_scope, creator_id, id, status, description, created_at, updated_at) FROM stdin;
管理员角色	\N	1	4	1	1	t	管理员	2025-09-06 01:12:52.916162	2025-09-06 01:12:52.916163
普通角色	\N	2	1	1	2	t	普通角色	2025-09-06 01:12:52.916163	2025-09-06 01:12:52.916164
\.


--
-- Data for Name: system_role_depts; Type: TABLE DATA; Schema: public; Owner: tao
--

COPY public.system_role_depts (role_id, dept_id) FROM stdin;
1	1
2	1
2	6
\.


--
-- Data for Name: system_role_menus; Type: TABLE DATA; Schema: public; Owner: tao
--

COPY public.system_role_menus (role_id, menu_id) FROM stdin;
1	1
1	2
1	3
1	4
1	5
1	6
1	7
1	8
1	9
1	10
1	11
1	12
1	13
1	14
1	15
1	16
1	17
1	18
1	19
1	20
1	21
1	22
1	23
1	24
1	25
1	26
1	27
1	28
1	29
1	30
1	31
1	32
1	33
1	34
1	35
1	36
1	37
1	38
1	39
1	40
1	41
1	42
1	43
1	44
1	45
1	46
1	47
1	48
1	49
1	50
1	51
1	52
1	53
1	54
1	55
1	56
1	57
1	58
1	59
1	60
1	61
1	62
1	63
1	64
1	65
1	66
1	67
1	68
1	69
1	70
1	71
1	72
1	73
1	74
1	75
1	76
1	77
1	78
1	79
1	80
1	81
1	82
1	83
1	84
1	85
1	86
1	87
1	88
1	89
1	90
1	91
1	92
1	93
1	94
1	95
1	96
1	97
1	98
1	99
1	100
1	101
2	1
2	2
\.


--
-- Data for Name: system_user_positions; Type: TABLE DATA; Schema: public; Owner: tao
--

COPY public.system_user_positions (user_id, position_id) FROM stdin;
1	5
2	7
3	1
\.


--
-- Data for Name: system_user_roles; Type: TABLE DATA; Schema: public; Owner: tao
--

COPY public.system_user_roles (user_id, role_id) FROM stdin;
1	1
2	1
3	1
\.


--
-- Data for Name: system_users; Type: TABLE DATA; Schema: public; Owner: tao
--

COPY public.system_users (username, password, name, mobile, email, gender, avatar, is_superuser, last_login, dept_id, creator_id, id, status, description, created_at, updated_at) FROM stdin;
superadmin	$2b$12$/Df5YczDGF41zCh2F8Xbu.yHTJXGm3tONgsXz1KLUdG0mtpKUOLD2	超级管理员	15382112620	948080782@qq.com	1	https://service.fastapiadmin.com/api/v1/static/image/avatar.png	t	\N	1	\N	1	t	超级管理员	2025-09-06 01:12:52.914211	2025-09-06 01:12:52.914212
admin	$2b$12$e2IJgS/cvHgJ0H3G7Xa08OXoXnk6N/NX3IZRtubBDElA0VLZhkNOa	管理员	15382112222	admin@qq.com	0	https://service.fastapiadmin.com/api/v1/static/image/avatar.png	f	\N	1	1	2	t	管理员	2025-09-06 01:12:52.914212	2025-09-06 01:12:52.914213
demo	$2b$12$e2IJgS/cvHgJ0H3G7Xa08OXoXnk6N/NX3IZRtubBDElA0VLZhkNOa	演示用户	15382112121	demo@qq.com	1	https://service.fastapiadmin.com/api/v1/static/image/avatar.png	f	\N	6	1	3	t	演示用户	2025-09-06 01:12:52.914213	2025-09-06 01:12:52.914213
\.


--
-- Name: application_myapp_id_seq; Type: SEQUENCE SET; Schema: public; Owner: tao
--

SELECT pg_catalog.setval('public.application_myapp_id_seq', 1, false);


--
-- Name: example_demo_id_seq; Type: SEQUENCE SET; Schema: public; Owner: tao
--

SELECT pg_catalog.setval('public.example_demo_id_seq', 1, false);


--
-- Name: monitor_job_id_seq; Type: SEQUENCE SET; Schema: public; Owner: tao
--

SELECT pg_catalog.setval('public.monitor_job_id_seq', 1, false);


--
-- Name: monitor_job_log_id_seq; Type: SEQUENCE SET; Schema: public; Owner: tao
--

SELECT pg_catalog.setval('public.monitor_job_log_id_seq', 1, false);


--
-- Name: system_config_id_seq; Type: SEQUENCE SET; Schema: public; Owner: tao
--

SELECT pg_catalog.setval('public.system_config_id_seq', 1, false);


--
-- Name: system_dept_id_seq; Type: SEQUENCE SET; Schema: public; Owner: tao
--

SELECT pg_catalog.setval('public.system_dept_id_seq', 1, false);


--
-- Name: system_dict_data_id_seq; Type: SEQUENCE SET; Schema: public; Owner: tao
--

SELECT pg_catalog.setval('public.system_dict_data_id_seq', 1, false);


--
-- Name: system_dict_type_id_seq; Type: SEQUENCE SET; Schema: public; Owner: tao
--

SELECT pg_catalog.setval('public.system_dict_type_id_seq', 1, false);


--
-- Name: system_log_id_seq; Type: SEQUENCE SET; Schema: public; Owner: tao
--

SELECT pg_catalog.setval('public.system_log_id_seq', 1, false);


--
-- Name: system_menu_id_seq; Type: SEQUENCE SET; Schema: public; Owner: tao
--

SELECT pg_catalog.setval('public.system_menu_id_seq', 1, false);


--
-- Name: system_notice_id_seq; Type: SEQUENCE SET; Schema: public; Owner: tao
--

SELECT pg_catalog.setval('public.system_notice_id_seq', 1, false);


--
-- Name: system_position_id_seq; Type: SEQUENCE SET; Schema: public; Owner: tao
--

SELECT pg_catalog.setval('public.system_position_id_seq', 1, false);


--
-- Name: system_role_id_seq; Type: SEQUENCE SET; Schema: public; Owner: tao
--

SELECT pg_catalog.setval('public.system_role_id_seq', 1, false);


--
-- Name: system_users_id_seq; Type: SEQUENCE SET; Schema: public; Owner: tao
--

SELECT pg_catalog.setval('public.system_users_id_seq', 1, false);


--
-- Name: application_myapp application_myapp_name_key; Type: CONSTRAINT; Schema: public; Owner: tao
--

ALTER TABLE ONLY public.application_myapp
    ADD CONSTRAINT application_myapp_name_key UNIQUE (name);


--
-- Name: application_myapp application_myapp_pkey; Type: CONSTRAINT; Schema: public; Owner: tao
--

ALTER TABLE ONLY public.application_myapp
    ADD CONSTRAINT application_myapp_pkey PRIMARY KEY (id);


--
-- Name: example_demo example_demo_pkey; Type: CONSTRAINT; Schema: public; Owner: tao
--

ALTER TABLE ONLY public.example_demo
    ADD CONSTRAINT example_demo_pkey PRIMARY KEY (id);


--
-- Name: monitor_job_log monitor_job_log_pkey; Type: CONSTRAINT; Schema: public; Owner: tao
--

ALTER TABLE ONLY public.monitor_job_log
    ADD CONSTRAINT monitor_job_log_pkey PRIMARY KEY (id);


--
-- Name: monitor_job monitor_job_pkey; Type: CONSTRAINT; Schema: public; Owner: tao
--

ALTER TABLE ONLY public.monitor_job
    ADD CONSTRAINT monitor_job_pkey PRIMARY KEY (id);


--
-- Name: system_config system_config_config_key_key; Type: CONSTRAINT; Schema: public; Owner: tao
--

ALTER TABLE ONLY public.system_config
    ADD CONSTRAINT system_config_config_key_key UNIQUE (config_key);


--
-- Name: system_config system_config_config_name_key; Type: CONSTRAINT; Schema: public; Owner: tao
--

ALTER TABLE ONLY public.system_config
    ADD CONSTRAINT system_config_config_name_key UNIQUE (config_name);


--
-- Name: system_config system_config_pkey; Type: CONSTRAINT; Schema: public; Owner: tao
--

ALTER TABLE ONLY public.system_config
    ADD CONSTRAINT system_config_pkey PRIMARY KEY (id);


--
-- Name: system_dept system_dept_name_key; Type: CONSTRAINT; Schema: public; Owner: tao
--

ALTER TABLE ONLY public.system_dept
    ADD CONSTRAINT system_dept_name_key UNIQUE (name);


--
-- Name: system_dept system_dept_pkey; Type: CONSTRAINT; Schema: public; Owner: tao
--

ALTER TABLE ONLY public.system_dept
    ADD CONSTRAINT system_dept_pkey PRIMARY KEY (id);


--
-- Name: system_dict_data system_dict_data_pkey; Type: CONSTRAINT; Schema: public; Owner: tao
--

ALTER TABLE ONLY public.system_dict_data
    ADD CONSTRAINT system_dict_data_pkey PRIMARY KEY (id);


--
-- Name: system_dict_type system_dict_type_dict_name_key; Type: CONSTRAINT; Schema: public; Owner: tao
--

ALTER TABLE ONLY public.system_dict_type
    ADD CONSTRAINT system_dict_type_dict_name_key UNIQUE (dict_name);


--
-- Name: system_dict_type system_dict_type_dict_type_key; Type: CONSTRAINT; Schema: public; Owner: tao
--

ALTER TABLE ONLY public.system_dict_type
    ADD CONSTRAINT system_dict_type_dict_type_key UNIQUE (dict_type);


--
-- Name: system_dict_type system_dict_type_pkey; Type: CONSTRAINT; Schema: public; Owner: tao
--

ALTER TABLE ONLY public.system_dict_type
    ADD CONSTRAINT system_dict_type_pkey PRIMARY KEY (id);


--
-- Name: system_log system_log_pkey; Type: CONSTRAINT; Schema: public; Owner: tao
--

ALTER TABLE ONLY public.system_log
    ADD CONSTRAINT system_log_pkey PRIMARY KEY (id);


--
-- Name: system_menu system_menu_name_key; Type: CONSTRAINT; Schema: public; Owner: tao
--

ALTER TABLE ONLY public.system_menu
    ADD CONSTRAINT system_menu_name_key UNIQUE (name);


--
-- Name: system_menu system_menu_pkey; Type: CONSTRAINT; Schema: public; Owner: tao
--

ALTER TABLE ONLY public.system_menu
    ADD CONSTRAINT system_menu_pkey PRIMARY KEY (id);


--
-- Name: system_notice system_notice_pkey; Type: CONSTRAINT; Schema: public; Owner: tao
--

ALTER TABLE ONLY public.system_notice
    ADD CONSTRAINT system_notice_pkey PRIMARY KEY (id);


--
-- Name: system_position system_position_name_key; Type: CONSTRAINT; Schema: public; Owner: tao
--

ALTER TABLE ONLY public.system_position
    ADD CONSTRAINT system_position_name_key UNIQUE (name);


--
-- Name: system_position system_position_pkey; Type: CONSTRAINT; Schema: public; Owner: tao
--

ALTER TABLE ONLY public.system_position
    ADD CONSTRAINT system_position_pkey PRIMARY KEY (id);


--
-- Name: system_role system_role_code_key; Type: CONSTRAINT; Schema: public; Owner: tao
--

ALTER TABLE ONLY public.system_role
    ADD CONSTRAINT system_role_code_key UNIQUE (code);


--
-- Name: system_role_depts system_role_depts_pkey; Type: CONSTRAINT; Schema: public; Owner: tao
--

ALTER TABLE ONLY public.system_role_depts
    ADD CONSTRAINT system_role_depts_pkey PRIMARY KEY (role_id, dept_id);


--
-- Name: system_role_menus system_role_menus_pkey; Type: CONSTRAINT; Schema: public; Owner: tao
--

ALTER TABLE ONLY public.system_role_menus
    ADD CONSTRAINT system_role_menus_pkey PRIMARY KEY (role_id, menu_id);


--
-- Name: system_role system_role_name_key; Type: CONSTRAINT; Schema: public; Owner: tao
--

ALTER TABLE ONLY public.system_role
    ADD CONSTRAINT system_role_name_key UNIQUE (name);


--
-- Name: system_role system_role_pkey; Type: CONSTRAINT; Schema: public; Owner: tao
--

ALTER TABLE ONLY public.system_role
    ADD CONSTRAINT system_role_pkey PRIMARY KEY (id);


--
-- Name: system_user_positions system_user_positions_pkey; Type: CONSTRAINT; Schema: public; Owner: tao
--

ALTER TABLE ONLY public.system_user_positions
    ADD CONSTRAINT system_user_positions_pkey PRIMARY KEY (user_id, position_id);


--
-- Name: system_user_roles system_user_roles_pkey; Type: CONSTRAINT; Schema: public; Owner: tao
--

ALTER TABLE ONLY public.system_user_roles
    ADD CONSTRAINT system_user_roles_pkey PRIMARY KEY (user_id, role_id);


--
-- Name: system_users system_users_email_key; Type: CONSTRAINT; Schema: public; Owner: tao
--

ALTER TABLE ONLY public.system_users
    ADD CONSTRAINT system_users_email_key UNIQUE (email);


--
-- Name: system_users system_users_mobile_key; Type: CONSTRAINT; Schema: public; Owner: tao
--

ALTER TABLE ONLY public.system_users
    ADD CONSTRAINT system_users_mobile_key UNIQUE (mobile);


--
-- Name: system_users system_users_pkey; Type: CONSTRAINT; Schema: public; Owner: tao
--

ALTER TABLE ONLY public.system_users
    ADD CONSTRAINT system_users_pkey PRIMARY KEY (id);


--
-- Name: system_users system_users_username_key; Type: CONSTRAINT; Schema: public; Owner: tao
--

ALTER TABLE ONLY public.system_users
    ADD CONSTRAINT system_users_username_key UNIQUE (username);


--
-- Name: ix_application_myapp_creator_id; Type: INDEX; Schema: public; Owner: tao
--

CREATE INDEX ix_application_myapp_creator_id ON public.application_myapp USING btree (creator_id);


--
-- Name: ix_example_demo_creator_id; Type: INDEX; Schema: public; Owner: tao
--

CREATE INDEX ix_example_demo_creator_id ON public.example_demo USING btree (creator_id);


--
-- Name: ix_monitor_job_creator_id; Type: INDEX; Schema: public; Owner: tao
--

CREATE INDEX ix_monitor_job_creator_id ON public.monitor_job USING btree (creator_id);


--
-- Name: ix_system_config_creator_id; Type: INDEX; Schema: public; Owner: tao
--

CREATE INDEX ix_system_config_creator_id ON public.system_config USING btree (creator_id);


--
-- Name: ix_system_dept_parent_id; Type: INDEX; Schema: public; Owner: tao
--

CREATE INDEX ix_system_dept_parent_id ON public.system_dept USING btree (parent_id);


--
-- Name: ix_system_dict_data_creator_id; Type: INDEX; Schema: public; Owner: tao
--

CREATE INDEX ix_system_dict_data_creator_id ON public.system_dict_data USING btree (creator_id);


--
-- Name: ix_system_dict_type_creator_id; Type: INDEX; Schema: public; Owner: tao
--

CREATE INDEX ix_system_dict_type_creator_id ON public.system_dict_type USING btree (creator_id);


--
-- Name: ix_system_log_creator_id; Type: INDEX; Schema: public; Owner: tao
--

CREATE INDEX ix_system_log_creator_id ON public.system_log USING btree (creator_id);


--
-- Name: ix_system_menu_parent_id; Type: INDEX; Schema: public; Owner: tao
--

CREATE INDEX ix_system_menu_parent_id ON public.system_menu USING btree (parent_id);


--
-- Name: ix_system_notice_creator_id; Type: INDEX; Schema: public; Owner: tao
--

CREATE INDEX ix_system_notice_creator_id ON public.system_notice USING btree (creator_id);


--
-- Name: ix_system_position_creator_id; Type: INDEX; Schema: public; Owner: tao
--

CREATE INDEX ix_system_position_creator_id ON public.system_position USING btree (creator_id);


--
-- Name: ix_system_role_creator_id; Type: INDEX; Schema: public; Owner: tao
--

CREATE INDEX ix_system_role_creator_id ON public.system_role USING btree (creator_id);


--
-- Name: ix_system_users_creator_id; Type: INDEX; Schema: public; Owner: tao
--

CREATE INDEX ix_system_users_creator_id ON public.system_users USING btree (creator_id);


--
-- Name: ix_system_users_dept_id; Type: INDEX; Schema: public; Owner: tao
--

CREATE INDEX ix_system_users_dept_id ON public.system_users USING btree (dept_id);


--
-- Name: monitor_job_log monitor_job_log_job_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: tao
--

ALTER TABLE ONLY public.monitor_job_log
    ADD CONSTRAINT monitor_job_log_job_id_fkey FOREIGN KEY (job_id) REFERENCES public.monitor_job(id);


--
-- Name: system_dept system_dept_parent_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: tao
--

ALTER TABLE ONLY public.system_dept
    ADD CONSTRAINT system_dept_parent_id_fkey FOREIGN KEY (parent_id) REFERENCES public.system_dept(id) ON UPDATE CASCADE ON DELETE CASCADE;


--
-- Name: system_dict_data system_dict_data_dict_type_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: tao
--

ALTER TABLE ONLY public.system_dict_data
    ADD CONSTRAINT system_dict_data_dict_type_id_fkey FOREIGN KEY (dict_type_id) REFERENCES public.system_dict_type(id);


--
-- Name: system_menu system_menu_parent_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: tao
--

ALTER TABLE ONLY public.system_menu
    ADD CONSTRAINT system_menu_parent_id_fkey FOREIGN KEY (parent_id) REFERENCES public.system_menu(id) ON DELETE SET NULL;


--
-- Name: system_role_depts system_role_depts_dept_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: tao
--

ALTER TABLE ONLY public.system_role_depts
    ADD CONSTRAINT system_role_depts_dept_id_fkey FOREIGN KEY (dept_id) REFERENCES public.system_dept(id) ON UPDATE CASCADE ON DELETE CASCADE;


--
-- Name: system_role_depts system_role_depts_role_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: tao
--

ALTER TABLE ONLY public.system_role_depts
    ADD CONSTRAINT system_role_depts_role_id_fkey FOREIGN KEY (role_id) REFERENCES public.system_role(id) ON UPDATE CASCADE ON DELETE CASCADE;


--
-- Name: system_role_menus system_role_menus_menu_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: tao
--

ALTER TABLE ONLY public.system_role_menus
    ADD CONSTRAINT system_role_menus_menu_id_fkey FOREIGN KEY (menu_id) REFERENCES public.system_menu(id) ON UPDATE CASCADE ON DELETE CASCADE;


--
-- Name: system_role_menus system_role_menus_role_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: tao
--

ALTER TABLE ONLY public.system_role_menus
    ADD CONSTRAINT system_role_menus_role_id_fkey FOREIGN KEY (role_id) REFERENCES public.system_role(id) ON UPDATE CASCADE ON DELETE CASCADE;


--
-- Name: system_user_positions system_user_positions_position_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: tao
--

ALTER TABLE ONLY public.system_user_positions
    ADD CONSTRAINT system_user_positions_position_id_fkey FOREIGN KEY (position_id) REFERENCES public.system_position(id) ON UPDATE CASCADE ON DELETE CASCADE;


--
-- Name: system_user_positions system_user_positions_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: tao
--

ALTER TABLE ONLY public.system_user_positions
    ADD CONSTRAINT system_user_positions_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.system_users(id) ON UPDATE CASCADE ON DELETE CASCADE;


--
-- Name: system_user_roles system_user_roles_role_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: tao
--

ALTER TABLE ONLY public.system_user_roles
    ADD CONSTRAINT system_user_roles_role_id_fkey FOREIGN KEY (role_id) REFERENCES public.system_role(id) ON UPDATE CASCADE ON DELETE CASCADE;


--
-- Name: system_user_roles system_user_roles_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: tao
--

ALTER TABLE ONLY public.system_user_roles
    ADD CONSTRAINT system_user_roles_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.system_users(id) ON UPDATE CASCADE ON DELETE CASCADE;


--
-- Name: system_users system_users_dept_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: tao
--

ALTER TABLE ONLY public.system_users
    ADD CONSTRAINT system_users_dept_id_fkey FOREIGN KEY (dept_id) REFERENCES public.system_dept(id) ON UPDATE CASCADE ON DELETE SET NULL;


--
-- PostgreSQL database dump complete
--

