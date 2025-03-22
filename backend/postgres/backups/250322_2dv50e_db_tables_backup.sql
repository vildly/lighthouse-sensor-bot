--
-- PostgreSQL database dump
--

-- Dumped from database version 17.2 (Debian 17.2-1.pgdg120+1)
-- Dumped by pg_dump version 17.2

-- Started on 2025-03-22 13:44:19 UTC

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
-- TOC entry 3390 (class 0 OID 0)
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
    factual_correctness numeric,
    semantic_similarity numeric,
    context_recall numeric,
    faithfulness numeric,
    bleu_score numeric,
    non_llm_string_similarity numeric,
    rogue_score numeric,
    string_present numeric,
    query_result_id integer
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
-- TOC entry 3391 (class 0 OID 0)
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
    query jsonb,
    direct_response jsonb,
    full_response jsonb,
    sql_queries jsonb,
    llm_model_id integer NOT NULL
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
-- TOC entry 3392 (class 0 OID 0)
-- Dependencies: 219
-- Name: query_result_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.query_result_id_seq OWNED BY public.query_result.id;


--
-- TOC entry 3220 (class 2604 OID 24581)
-- Name: llm_models id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.llm_models ALTER COLUMN id SET DEFAULT nextval('public.llm_models_id_seq'::regclass);


--
-- TOC entry 3222 (class 2604 OID 24604)
-- Name: query_evaluation id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.query_evaluation ALTER COLUMN id SET DEFAULT nextval('public.query_evaluation_id_seq'::regclass);


--
-- TOC entry 3221 (class 2604 OID 24595)
-- Name: query_result id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.query_result ALTER COLUMN id SET DEFAULT nextval('public.query_result_id_seq'::regclass);


--
-- TOC entry 3380 (class 0 OID 24578)
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
-- TOC entry 3384 (class 0 OID 24601)
-- Dependencies: 222
-- Data for Name: query_evaluation; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.query_evaluation (id, retrieved_contexts, reference, factual_correctness, semantic_similarity, context_recall, faithfulness, bleu_score, non_llm_string_similarity, rogue_score, string_present, query_result_id) FROM stdin;
\.


--
-- TOC entry 3382 (class 0 OID 24592)
-- Dependencies: 220
-- Data for Name: query_result; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.query_result (id, query, direct_response, full_response, sql_queries, llm_model_id) FROM stdin;
\.


--
-- TOC entry 3393 (class 0 OID 0)
-- Dependencies: 217
-- Name: llm_models_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.llm_models_id_seq', 20, true);


--
-- TOC entry 3394 (class 0 OID 0)
-- Dependencies: 221
-- Name: query_evaluation_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.query_evaluation_id_seq', 1, false);


--
-- TOC entry 3395 (class 0 OID 0)
-- Dependencies: 219
-- Name: query_result_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.query_result_id_seq', 1, false);


--
-- TOC entry 3225 (class 2606 OID 24583)
-- Name: llm_models llm_models_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.llm_models
    ADD CONSTRAINT llm_models_pkey PRIMARY KEY (id);


--
-- TOC entry 3231 (class 2606 OID 24608)
-- Name: query_evaluation query_evaluation_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.query_evaluation
    ADD CONSTRAINT query_evaluation_pkey PRIMARY KEY (id);


--
-- TOC entry 3229 (class 2606 OID 24599)
-- Name: query_result query_result_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.query_result
    ADD CONSTRAINT query_result_pkey PRIMARY KEY (id);


--
-- TOC entry 3227 (class 2606 OID 24590)
-- Name: llm_models unique_name; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.llm_models
    ADD CONSTRAINT unique_name UNIQUE (name);


--
-- TOC entry 3233 (class 2606 OID 24609)
-- Name: query_evaluation fk_query_evaluation_query_result_id; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.query_evaluation
    ADD CONSTRAINT fk_query_evaluation_query_result_id FOREIGN KEY (query_result_id) REFERENCES public.query_result(id) NOT VALID;


--
-- TOC entry 3232 (class 2606 OID 24614)
-- Name: query_result fk_query_result_llm_model_id_llm_models_id; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.query_result
    ADD CONSTRAINT fk_query_result_llm_model_id_llm_models_id FOREIGN KEY (llm_model_id) REFERENCES public.llm_models(id) NOT VALID;


-- Completed on 2025-03-22 13:44:19 UTC

--
-- PostgreSQL database dump complete
--

