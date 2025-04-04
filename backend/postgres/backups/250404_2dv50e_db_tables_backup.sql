--
-- PostgreSQL database dump
--

-- Dumped from database version 17.2 (Debian 17.2-1.pgdg120+1)
-- Dumped by pg_dump version 17.2

-- Started on 2025-04-04 13:23:00 UTC

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
-- TOC entry 222 (class 1259 OID 24601)
-- Name: query_evaluation; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.query_evaluation (
    id integer NOT NULL,
    query_result_id integer,
    evaluation_metrics_id integer,
    retrieved_contexts text,
    reference text
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
-- TOC entry 3378 (class 0 OID 0)
-- Dependencies: 221
-- Name: query_evaluation_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.query_evaluation_id_seq OWNED BY public.query_evaluation.id;


--
-- TOC entry 3221 (class 2604 OID 24604)
-- Name: query_evaluation id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.query_evaluation ALTER COLUMN id SET DEFAULT nextval('public.query_evaluation_id_seq'::regclass);


--
-- TOC entry 3372 (class 0 OID 24601)
-- Dependencies: 222
-- Data for Name: query_evaluation; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.query_evaluation (id, query_result_id, evaluation_metrics_id, retrieved_contexts, reference) FROM stdin;
\.


--
-- TOC entry 3379 (class 0 OID 0)
-- Dependencies: 221
-- Name: query_evaluation_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.query_evaluation_id_seq', 1, false);


--
-- TOC entry 3223 (class 2606 OID 24608)
-- Name: query_evaluation query_evaluation_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.query_evaluation
    ADD CONSTRAINT query_evaluation_pkey PRIMARY KEY (id);


--
-- TOC entry 3224 (class 2606 OID 24628)
-- Name: query_evaluation fk_query_evaluation_evaluation_metrics_id; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.query_evaluation
    ADD CONSTRAINT fk_query_evaluation_evaluation_metrics_id FOREIGN KEY (evaluation_metrics_id) REFERENCES public.evaluation_metrics(id) NOT VALID;


--
-- TOC entry 3225 (class 2606 OID 24609)
-- Name: query_evaluation fk_query_evaluation_query_result_id; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.query_evaluation
    ADD CONSTRAINT fk_query_evaluation_query_result_id FOREIGN KEY (query_result_id) REFERENCES public.query_result(id) NOT VALID;


-- Completed on 2025-04-04 13:23:00 UTC

--
-- PostgreSQL database dump complete
--

