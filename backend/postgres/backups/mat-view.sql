CREATE MATERIALIZED VIEW model_performance_metrics AS
SELECT 
    lm.id as model_id,
    lm.name as model_name,
    lm.type as model_type,
    AVG(em.factual_correctness) as avg_factual_correctness,
    AVG(em.semantic_similarity) as avg_semantic_similarity,
    AVG(em.context_recall) as avg_context_recall,
    AVG(em.faithfulness) as avg_faithfulness,
    AVG(em.bleu_score) as avg_bleu_score,
    AVG(em.non_llm_string_similarity) as avg_non_llm_string_similarity,
    AVG(em.rogue_score) as avg_rogue_score,
    AVG(em.string_present) as avg_string_present,
    COUNT(qr.id) as query_count
FROM 
    llm_models lm
LEFT JOIN 
    query_result qr ON lm.id = qr.llm_model_id
LEFT JOIN 
    query_evaluation qe ON qr.id = qe.query_result_id
LEFT JOIN 
    evaluation_metrics em ON qe.evaluation_metrics_id = em.id
GROUP BY 
    lm.id, lm.name, lm.type
WITH DATA;

-- Create an index for faster querying
CREATE UNIQUE INDEX model_performance_metrics_idx ON model_performance_metrics (model_id);

-- Function to refresh the materialized view
CREATE OR REPLACE FUNCTION refresh_model_performance_metrics()
RETURNS TRIGGER AS $$
BEGIN
    REFRESH MATERIALIZED VIEW model_performance_metrics;
    RETURN NULL;
END;
$$ LANGUAGE plpgsql;

-- Trigger to refresh the view when evaluation metrics are updated
CREATE TRIGGER refresh_model_performance_metrics_trigger
AFTER INSERT OR UPDATE OR DELETE ON evaluation_metrics
FOR EACH STATEMENT
EXECUTE FUNCTION refresh_model_performance_metrics();