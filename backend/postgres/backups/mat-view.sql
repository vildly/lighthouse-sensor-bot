DROP MATERIALIZED VIEW IF EXISTS model_performance_metrics;

CREATE MATERIALIZED VIEW model_performance_metrics AS
SELECT
    lm.id as model_id,
    lm.name as model_name,
    lm.type as model_type,
    AVG(em.factual_correctness) FILTER (WHERE em.factual_correctness IS NOT NULL) as avg_factual_correctness,
    AVG(em.semantic_similarity) FILTER (WHERE em.semantic_similarity IS NOT NULL) as avg_semantic_similarity,
    AVG(em.context_recall) FILTER (WHERE em.context_recall IS NOT NULL) as avg_context_recall,
    AVG(em.faithfulness) FILTER (WHERE em.faithfulness IS NOT NULL) as avg_faithfulness,
    AVG(em.bleu_score) FILTER (WHERE em.bleu_score IS NOT NULL) as avg_bleu_score,
    AVG(em.non_llm_string_similarity) FILTER (WHERE em.non_llm_string_similarity IS NOT NULL) as avg_non_llm_string_similarity,
    AVG(em.rogue_score) FILTER (WHERE em.rogue_score IS NOT NULL) as avg_rogue_score,
    AVG(em.string_present) FILTER (WHERE em.string_present IS NOT NULL) as avg_string_present,
    COUNT(qe.id) as query_evaluation_count
FROM
    llm_models lm
INNER JOIN
    query_result qr ON lm.id = qr.llm_model_id
INNER JOIN
    query_evaluation qe ON qr.id = qe.query_result_id
LEFT JOIN
    evaluation_metrics em ON qe.evaluation_metrics_id = em.id
GROUP BY
    lm.id, lm.name, lm.type
WITH DATA;

-- Re-create the index
DROP INDEX IF EXISTS model_performance_metrics_idx;
CREATE UNIQUE INDEX model_performance_metrics_idx ON model_performance_metrics (model_id);

DROP TRIGGER IF EXISTS refresh_model_performance_metrics_trigger ON query_evaluation;

CREATE OR REPLACE FUNCTION refresh_model_performance_metrics()
RETURNS TRIGGER AS $$
BEGIN
    REFRESH MATERIALIZED VIEW model_performance_metrics;
    RETURN NULL;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER refresh_model_performance_metrics_trigger
AFTER INSERT OR UPDATE OR DELETE ON query_evaluation
FOR EACH STATEMENT
EXECUTE FUNCTION refresh_model_performance_metrics();