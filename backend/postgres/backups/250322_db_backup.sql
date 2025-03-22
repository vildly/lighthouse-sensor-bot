--
-- PostgreSQL database dump
--

-- Dumped from database version 17.2 (Debian 17.2-1.pgdg120+1)
-- Dumped by pg_dump version 17.2

-- Started on 2025-03-22 18:17:23 UTC

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
-- TOC entry 224 (class 1259 OID 24620)
-- Name: evaluation_metrics; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.evaluation_metrics (
    id integer NOT NULL,
    factuall_correctness numeric,
    semantic_similarity numeric,
    context_recall numeric,
    faithfulness numeric,
    bleu_score numeric,
    non_llm_string_similarity numeric,
    rogue_score numeric,
    string_present numeric
);


ALTER TABLE public.evaluation_metrics OWNER TO postgres;

--
-- TOC entry 223 (class 1259 OID 24619)
-- Name: evaluation_metrics_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.evaluation_metrics_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.evaluation_metrics_id_seq OWNER TO postgres;

--
-- TOC entry 3401 (class 0 OID 0)
-- Dependencies: 223
-- Name: evaluation_metrics_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.evaluation_metrics_id_seq OWNED BY public.evaluation_metrics.id;


--
-- TOC entry 218 (class 1259 OID 24578)
-- Name: llm_models; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.llm_models (
    id integer NOT NULL,
    name character varying(255) NOT NULL,
    type character varying NOT NULL,
    CONSTRAINT type_check CHECK (((type)::text = ANY ((ARRAY['proprietary'::character varying, 'open source'::character varying])::text[])))
);


ALTER TABLE public.llm_models OWNER TO postgres;

--
-- TOC entry 217 (class 1259 OID 24577)
-- Name: llm_models_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.llm_models_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.llm_models_id_seq OWNER TO postgres;

--
-- TOC entry 3402 (class 0 OID 0)
-- Dependencies: 217
-- Name: llm_models_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.llm_models_id_seq OWNED BY public.llm_models.id;


--
-- TOC entry 222 (class 1259 OID 24601)
-- Name: query_evaluation; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.query_evaluation (
    id integer NOT NULL,
    retrieved_contexts jsonb,
    reference jsonb,
    query_result_id integer,
    evaluation_metrics_id integer
);


ALTER TABLE public.query_evaluation OWNER TO postgres;

--
-- TOC entry 221 (class 1259 OID 24600)
-- Name: query_evaluation_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.query_evaluation_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.query_evaluation_id_seq OWNER TO postgres;

--
-- TOC entry 3403 (class 0 OID 0)
-- Dependencies: 221
-- Name: query_evaluation_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.query_evaluation_id_seq OWNED BY public.query_evaluation.id;


--
-- TOC entry 220 (class 1259 OID 24592)
-- Name: query_result; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.query_result (
    id integer NOT NULL,
    llm_model_id integer NOT NULL,
    query text,
    direct_response text,
    full_response text,
    sql_queries text
);


ALTER TABLE public.query_result OWNER TO postgres;

--
-- TOC entry 219 (class 1259 OID 24591)
-- Name: query_result_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.query_result_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.query_result_id_seq OWNER TO postgres;

--
-- TOC entry 3404 (class 0 OID 0)
-- Dependencies: 219
-- Name: query_result_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.query_result_id_seq OWNED BY public.query_result.id;


--
-- TOC entry 3228 (class 2604 OID 24623)
-- Name: evaluation_metrics id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.evaluation_metrics ALTER COLUMN id SET DEFAULT nextval('public.evaluation_metrics_id_seq'::regclass);


--
-- TOC entry 3225 (class 2604 OID 24581)
-- Name: llm_models id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.llm_models ALTER COLUMN id SET DEFAULT nextval('public.llm_models_id_seq'::regclass);


--
-- TOC entry 3227 (class 2604 OID 24604)
-- Name: query_evaluation id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.query_evaluation ALTER COLUMN id SET DEFAULT nextval('public.query_evaluation_id_seq'::regclass);


--
-- TOC entry 3226 (class 2604 OID 24595)
-- Name: query_result id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.query_result ALTER COLUMN id SET DEFAULT nextval('public.query_result_id_seq'::regclass);


--
-- TOC entry 3395 (class 0 OID 24620)
-- Dependencies: 224
-- Data for Name: evaluation_metrics; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.evaluation_metrics (id, factuall_correctness, semantic_similarity, context_recall, faithfulness, bleu_score, non_llm_string_similarity, rogue_score, string_present) FROM stdin;
\.


--
-- TOC entry 3389 (class 0 OID 24578)
-- Dependencies: 218
-- Data for Name: llm_models; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.llm_models (id, name, type) FROM stdin;
6	openai/gpt-4o-2024-11-20	proprietary
12	anthropic/claude-3.7-sonnet	proprietary
13	google/gemini-2.0-flash-001	proprietary
14	amazon/nova-pro-v1	proprietary
15	qwen/qwen-2.5-72b-instruct	open source
16	meta-llama/llama-3.3-70b-instruct	open source
17	meta-llama/llama-3.1-8b-instruct	open source
18	mistralai/ministral-8b	open source
\.


--
-- TOC entry 3393 (class 0 OID 24601)
-- Dependencies: 222
-- Data for Name: query_evaluation; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.query_evaluation (id, retrieved_contexts, reference, query_result_id, evaluation_metrics_id) FROM stdin;
\.


--
-- TOC entry 3391 (class 0 OID 24592)
-- Dependencies: 220
-- Data for Name: query_result; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.query_result (id, llm_model_id, query, direct_response, full_response, sql_queries) FROM stdin;
1	15	What is the average speed of ferry Jupiter in knots? (Use data from ferry_trips_data.csv)	## Analysis\nTo calculate the average speed of the ferry Jupiter in knots, I need to use the formula: `speed = distance / time`.	## Analysis\nTo calculate the average speed of the ferry Jupiter in knots, I need to use the formula: `speed = distance / time`. The distance and time can be found in the `ferry_trips_data.csv` file. Specifically, I will use the `distance_outbound_nm` and `distance_inbound_nm` columns for distance, and the `time_departure` and `end_time_outbound` or `end_time_inbound` columns for time.\n\nI will first check if the `ferry_trips_data` table exists using the `show_tables` function. If it does not exist, I will create it using the `create_table_from_path` function.\n\nThen, I will write a query to calculate the average speed of the ferry Jupiter by filtering the data for the `Jupiter` ferry, calculating the time difference between `time_departure` and `end_time_outbound` or `end_time_inbound`, and dividing the distance by the time difference in hours.\n\n### Steps:\n1. Check if the `ferry_trips_data` table exists.\n2. If it does not exist, create it.\n3. Run the query to calculate the average speed of the ferry Jupiter.\n\n### Functions to call:\n1. `show_tables`\n2. `create_table_from_path` (if the table does not exist)\n3. `run_query` to execute the query\n\n	{"SHOW TABLES"}
2	15	What is the average speed of ferry Jupiter in knots? (Use data from ferry_trips_data.csv)	The average speed of the ferry Jupiter in knots is approximately 6.17 knots.	## Analysis\nTo calculate the average speed of the ferry Jupiter in knots, the following steps will be taken:\n1. Confirm the existence of the `ferry_trips_data` table.\n2. If the table does not exist, create it from the `ferry_trips_data.csv` file.\n3. Write a query to compute the average speed using the distance and time difference for the `Jupiter` ferry.\n4. Ensure the query accounts for null values and limits the result to 10 entries if that is desired.\n5. The speed will be calculated as distance in nautical miles divided by the time difference in hours, where time difference in hours is calculated from `start_time_outbound` and `end_time_outbound` fields.\n6. Run the query to get the result and present it.\n\nFirst, I will check if the `ferry_trips_data` table exists in the database using `show_tables`.\n\n## Analysis\nThe `ferry_trips_data` table has been successfully created. Now I will write and run a query to calculate the average speed of the ferry `Jupiter` in knots.\n\nThe query will:\n1. Filter for trips made by the ferry `Jupiter`.\n2. Calculate the time difference in hours between `start_time_outbound` and `end_time_outbound`.\n3. Calculate the speed in knots by dividing the distance in nautical miles by the time difference in hours.\n4. Compute the average of these speeds.\n5. Ensure null values are handled appropriately.\n\nHere is the query:\n```sql\nSELECT \n    AVG((distance_outbound_nm - distance_inbound_nm) / NULLIF((EXTRACT(EPOCH FROM (end_time_outbound::TIMESTAMP - start_time_outbound::TIMESTAMP))) / 3600.0, 0)) AS average_speed_knots\nFROM \n    ferry_trips_data\nWHERE \n    ferry_name = 'Jupiter';\n```\n\nNow I will run the query.\n\n\n## Analysis\nThe query executed successfully, but the result indicates a negative average speed, which is not physically meaningful. This suggests that there might be an issue with the way distances are being calculated. \n\nLet's modify the query to ensure we only consider positive distances and valid time differences. We will also ensure that the `distance_outbound_nm` is always positive.\n\nHere is the revised query:\n```sql\nSELECT \n    AVG(distance_outbound_nm / NULLIF((EXTRACT(EPOCH FROM (end_time_outbound::TIMESTAMP - start_time_outbound::TIMESTAMP))) / 3600.0, 0)) AS average_speed_knots\nFROM \n    ferry_trips_data\nWHERE \n    ferry_name = 'Jupiter' \n    AND distance_outbound_nm > 0 \n    AND start_time_outbound::TIMESTAMP < end_time_outbound::TIMESTAMP;\n```\n\nNow I will run the revised query.\n\n\n\n## Analysis\nThe revised query executed successfully and returned a meaningful average speed for the ferry `Jupiter`. The average speed of the ferry `Jupiter` in knots is approximately 6.17 knots.\n\nHere is the SQL query that was run:\n```sql\nSELECT \n    AVG(distance_outbound_nm / NULLIF((EXTRACT(EPOCH FROM (end_time_outbound::TIMESTAMP - start_time_outbound::TIMESTAMP))) / 3600.0, 0)) AS average_speed_knots\nFROM \n    ferry_trips_data\nWHERE \n    ferry_name = 'Jupiter' \n    AND distance_outbound_nm > 0 \n    AND start_time_outbound::TIMESTAMP < end_time_outbound::TIMESTAMP;\n```\n\n## Answer\nThe average speed of the ferry Jupiter in knots is approximately 6.17 knots.	{"SHOW TABLES Using path from semantic model for table ferry_trips_data: ferry_trips_data.csv","CREATE OR REPLACE TABLE 'ferry_trips_data' AS SELECT * FROM '/home/melke/lnu/2dv50e/lighthouse-sensor-bot/backend/data/ferry_trips_data.csv'","SELECT AVG((distance_outbound_nm - distance_inbound_nm) / NULLIF((EXTRACT(EPOCH FROM (end_time_outbound::TIMESTAMP - start_time_outbound::TIMESTAMP))) / 3600.0, 0)) AS average_speed_knots FROM ferry_trips_data WHERE ferry_name = 'Jupiter'","SELECT AVG(distance_outbound_nm / NULLIF((EXTRACT(EPOCH FROM (end_time_outbound::TIMESTAMP - start_time_outbound::TIMESTAMP))) / 3600.0, 0)) AS average_speed_knots FROM ferry_trips_data WHERE ferry_name = 'Jupiter' AND distance_outbound_nm > 0 AND start_time_outbound::TIMESTAMP < end_time_outbound::TIMESTAMP"}
\.


--
-- TOC entry 3405 (class 0 OID 0)
-- Dependencies: 223
-- Name: evaluation_metrics_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.evaluation_metrics_id_seq', 1, false);


--
-- TOC entry 3406 (class 0 OID 0)
-- Dependencies: 217
-- Name: llm_models_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.llm_models_id_seq', 20, true);


--
-- TOC entry 3407 (class 0 OID 0)
-- Dependencies: 221
-- Name: query_evaluation_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.query_evaluation_id_seq', 1, false);


--
-- TOC entry 3408 (class 0 OID 0)
-- Dependencies: 219
-- Name: query_result_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.query_result_id_seq', 2, true);


--
-- TOC entry 3239 (class 2606 OID 24627)
-- Name: evaluation_metrics evaluation_metrics_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.evaluation_metrics
    ADD CONSTRAINT evaluation_metrics_pkey PRIMARY KEY (id);


--
-- TOC entry 3231 (class 2606 OID 24583)
-- Name: llm_models llm_models_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.llm_models
    ADD CONSTRAINT llm_models_pkey PRIMARY KEY (id);


--
-- TOC entry 3237 (class 2606 OID 24608)
-- Name: query_evaluation query_evaluation_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.query_evaluation
    ADD CONSTRAINT query_evaluation_pkey PRIMARY KEY (id);


--
-- TOC entry 3235 (class 2606 OID 24599)
-- Name: query_result query_result_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.query_result
    ADD CONSTRAINT query_result_pkey PRIMARY KEY (id);


--
-- TOC entry 3233 (class 2606 OID 24590)
-- Name: llm_models unique_name; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.llm_models
    ADD CONSTRAINT unique_name UNIQUE (name);


--
-- TOC entry 3241 (class 2606 OID 24628)
-- Name: query_evaluation fk_query_evaluation_evaluation_metrics_id; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.query_evaluation
    ADD CONSTRAINT fk_query_evaluation_evaluation_metrics_id FOREIGN KEY (evaluation_metrics_id) REFERENCES public.evaluation_metrics(id) NOT VALID;


--
-- TOC entry 3242 (class 2606 OID 24609)
-- Name: query_evaluation fk_query_evaluation_query_result_id; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.query_evaluation
    ADD CONSTRAINT fk_query_evaluation_query_result_id FOREIGN KEY (query_result_id) REFERENCES public.query_result(id) NOT VALID;


--
-- TOC entry 3240 (class 2606 OID 24614)
-- Name: query_result fk_query_result_llm_model_id_llm_models_id; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.query_result
    ADD CONSTRAINT fk_query_result_llm_model_id_llm_models_id FOREIGN KEY (llm_model_id) REFERENCES public.llm_models(id) NOT VALID;


-- Completed on 2025-03-22 18:17:23 UTC

--
-- PostgreSQL database dump complete
--

