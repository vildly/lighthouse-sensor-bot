#!/usr/bin/env python3
"""
Test Results Viewer - View evaluation results from PostgreSQL database
"""

import argparse
import os
import pandas as pd
import psycopg2
from dotenv import load_dotenv
from tabulate import tabulate
from contextlib import contextmanager

# Load environment variables
load_dotenv()

@contextmanager
def get_db_cursor():
    """Get database cursor with environment-aware connection"""
    connection = None
    cursor = None
    
    # Database connection parameters
    db_params = {
        'port': int(os.getenv('DB_PORT', 5432)),
        'database': os.getenv('POSTGRES_DB', 'sensor_bot_db'),
        'user': os.getenv('POSTGRES_USER', 'sensor_bot'),
        'password': os.getenv('POSTGRES_PASSWORD', 'local_dev_password')
    }
    
    # Try different hosts (Docker service name first, then localhost options)
    hosts_to_try = [
        os.getenv('DB_HOST', 'postgres'),  # Docker service name
        'localhost',                        # Local development
        '127.0.0.1'                        # Alternative localhost
    ]
    
    for host in hosts_to_try:
        try:
            db_params['host'] = host
            connection = psycopg2.connect(**db_params)
            cursor = connection.cursor()
            break
        except Exception as e:
            if host == hosts_to_try[-1]:  # Last attempt failed
                raise Exception(f"Could not connect to database. Tried hosts: {hosts_to_try}. Last error: {e}")
            continue
    
    try:
        yield cursor
    finally:
        if cursor:
            cursor.close()
        if connection:
            connection.close()

def get_recent_results(limit=20):
    """Get recent test results with evaluation metrics"""
    with get_db_cursor() as cursor:
        cursor.execute("""
            SELECT 
                qr.test_no,
                qr.id as query_id,
                m.name as model_name,
                qr.timestamp::date || ' ' || qr.timestamp::time::varchar(5) as timestamp,
                qr.tool_calls,
                em.factual_correctness,
                em.semantic_similarity,
                em.context_recall,
                em.faithfulness,
                tu.total_tokens
            FROM query_result qr
            JOIN llm_models m ON qr.llm_model_id = m.id
            LEFT JOIN query_evaluation qe ON qr.id = qe.query_result_id
            LEFT JOIN evaluation_metrics em ON qe.evaluation_metrics_id = em.id
            LEFT JOIN token_usage tu ON qr.id = tu.query_result_id
            ORDER BY qr.timestamp DESC
            LIMIT %s
        """, (limit,))
        
        columns = [desc[0] for desc in cursor.description]
        results = cursor.fetchall()
        
        if not results:
            return pd.DataFrame()
            
        df = pd.DataFrame(results, columns=columns)
        return df

def get_model_performance_summary():
    """Get aggregated performance metrics by model"""
    with get_db_cursor() as cursor:
        cursor.execute("""
            SELECT 
                m.name as model_name,
                m.type as model_type,
                COUNT(qr.id) as query_evaluation_count,
                AVG(em.factual_correctness) as avg_factual_correctness,
                AVG(em.semantic_similarity) as avg_semantic_similarity,
                AVG(em.context_recall) as avg_context_recall,
                AVG(em.faithfulness) as avg_faithfulness,
                AVG(tu.total_tokens) as avg_total_tokens
            FROM llm_models m
            LEFT JOIN query_result qr ON m.id = qr.llm_model_id
            LEFT JOIN query_evaluation qe ON qr.id = qe.query_result_id
            LEFT JOIN evaluation_metrics em ON qe.evaluation_metrics_id = em.id
            LEFT JOIN token_usage tu ON qr.id = tu.query_result_id
            WHERE qr.id IS NOT NULL
            GROUP BY m.id, m.name, m.type
            ORDER BY query_evaluation_count DESC
        """)
        
        columns = [desc[0] for desc in cursor.description]
        results = cursor.fetchall()
        
        if not results:
            return pd.DataFrame()
            
        df = pd.DataFrame(results, columns=columns)
        return df

def get_detailed_results(limit=10):
    """Get detailed results including query text and responses"""
    with get_db_cursor() as cursor:
        cursor.execute("""
            SELECT 
                qr.test_no,
                qr.id as query_id,
                m.name as model_name,
                qr.timestamp,
                qr.query as query_text,
                qr.direct_response as response_text,
                qr.tool_calls,
                em.factual_correctness,
                em.semantic_similarity,
                em.context_recall,
                em.faithfulness,
                tu.total_tokens,
                tu.prompt_tokens,
                tu.completion_tokens
            FROM query_result qr
            JOIN llm_models m ON qr.llm_model_id = m.id
            LEFT JOIN query_evaluation qe ON qr.id = qe.query_result_id
            LEFT JOIN evaluation_metrics em ON qe.evaluation_metrics_id = em.id
            LEFT JOIN token_usage tu ON qr.id = tu.query_result_id
            ORDER BY qr.timestamp DESC
            LIMIT %s
        """, (limit,))
        
        columns = [desc[0] for desc in cursor.description]
        results = cursor.fetchall()
        
        if not results:
            return pd.DataFrame()
            
        df = pd.DataFrame(results, columns=columns)
        return df

def get_model_results(model_name, limit=20):
    """Get results for a specific model"""
    with get_db_cursor() as cursor:
        cursor.execute("""
            SELECT 
                qr.test_no,
                qr.id as query_id,
                m.name as model_name,
                qr.timestamp::date || ' ' || qr.timestamp::time::varchar(5) as timestamp,
                qr.tool_calls,
                em.factual_correctness,
                em.semantic_similarity,
                em.context_recall,
                em.faithfulness,
                tu.total_tokens
            FROM query_result qr
            JOIN llm_models m ON qr.llm_model_id = m.id
            LEFT JOIN query_evaluation qe ON qr.id = qe.query_result_id
            LEFT JOIN evaluation_metrics em ON qe.evaluation_metrics_id = em.id
            LEFT JOIN token_usage tu ON qr.id = tu.query_result_id
            WHERE m.name = %s
            ORDER BY qr.timestamp DESC
            LIMIT %s
        """, (model_name, limit))
        
        columns = [desc[0] for desc in cursor.description]
        results = cursor.fetchall()
        
        if not results:
            return pd.DataFrame()
            
        df = pd.DataFrame(results, columns=columns)
        return df

def get_available_models():
    """Get list of available models"""
    with get_db_cursor() as cursor:
        cursor.execute("""
            SELECT DISTINCT m.name
            FROM llm_models m
            JOIN query_result qr ON m.id = qr.llm_model_id
            ORDER BY m.name
        """)
        
        results = cursor.fetchall()
        return [row[0] for row in results]

def get_test_statistics():
    """Get overall test statistics"""
    with get_db_cursor() as cursor:
        cursor.execute("""
            SELECT 
                COUNT(DISTINCT qr.id) as total_queries,
                COUNT(DISTINCT m.name) as models_tested,
                MIN(qr.timestamp) as earliest_test,
                MAX(qr.timestamp) as latest_test,
                AVG(em.factual_correctness) as avg_factual_correctness,
                AVG(em.semantic_similarity) as avg_semantic_similarity,
                AVG(em.context_recall) as avg_context_recall,
                AVG(em.faithfulness) as avg_faithfulness
            FROM query_result qr
            JOIN llm_models m ON qr.llm_model_id = m.id
            LEFT JOIN query_evaluation qe ON qr.id = qe.query_result_id
            LEFT JOIN evaluation_metrics em ON qe.evaluation_metrics_id = em.id
        """)
        
        result = cursor.fetchone()
        if not result:
            return None
            
        columns = [desc[0] for desc in cursor.description]
        return dict(zip(columns, result))

def display_results_table(df, title="Results"):
    """Display results in a formatted table"""
    if df.empty:
        print(f"❌ No results found")
        return
        
    print(f"\n📊 {title} ({len(df)} entries):")
    print("=" * 80)
    
    # Format numeric columns to 3 decimal places
    numeric_cols = df.select_dtypes(include=['float64', 'int64']).columns
    for col in numeric_cols:
        if col not in ['query_id', 'test_no', 'total_tokens', 'prompt_tokens', 'completion_tokens']:
            df[col] = df[col].round(3)
    
    # Reorder columns to show test_no first if present
    if 'test_no' in df.columns:
        cols = ['test_no'] + [c for c in df.columns if c != 'test_no']
        df = df[cols]
    print(tabulate(df, headers='keys', tablefmt='grid', showindex=False))

def display_detailed_results(df):
    """Display detailed results with full text"""
    if df.empty:
        print("❌ No detailed results found")
        return
        
    print(f"\n📋 Detailed Results ({len(df)} entries):")
    print("=" * 80)
    
    for _, row in df.iterrows():
        test_no_str = f" | Test No: {row['test_no']}" if 'test_no' in row and pd.notna(row['test_no']) else ""
        print(f"\n🔍 Query ID: {row['query_id']} | Model: {row['model_name']}{test_no_str}")
        print(f"⏰ Timestamp: {row['timestamp']}")
        print(f"\n📝 Query: {row['query_text'][:200]}{'...' if len(str(row['query_text'])) > 200 else ''}")
        print(f"\n💬 Response: {row['response_text'][:300]}{'...' if len(str(row['response_text'])) > 300 else ''}")
        
        # Display tool calls if available
        if 'tool_calls' in row and pd.notna(row['tool_calls']) and row['tool_calls']:
            print(f"\n🔧 Tools Used: {row['tool_calls']}")
        else:
            print(f"\n🔧 Tools Used: None")
        
        print(f"\n📊 Metrics:")
        print(f"   • Factual Correctness: {row['factual_correctness']:.3f}" if pd.notna(row['factual_correctness']) else "   • Factual Correctness: N/A")
        print(f"   • Semantic Similarity: {row['semantic_similarity']:.3f}" if pd.notna(row['semantic_similarity']) else "   • Semantic Similarity: N/A")
        print(f"   • Context Recall: {row['context_recall']:.3f}" if pd.notna(row['context_recall']) else "   • Context Recall: N/A")
        print(f"   • Faithfulness: {row['faithfulness']:.3f}" if pd.notna(row['faithfulness']) else "   • Faithfulness: N/A")
        print(f"   • Total Tokens: {row['total_tokens']}" if pd.notna(row['total_tokens']) else "   • Total Tokens: N/A")
        
        print("-" * 60)

def main():
    parser = argparse.ArgumentParser(
        description="View evaluation test results from PostgreSQL database",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python view_test_results.py                    # Show recent results
  python view_test_results.py --summary          # Show model performance summary
  python view_test_results.py --detailed         # Show detailed results with full query text and responses
  python view_test_results.py --model gpt-4o     # Show results for specific model
  python view_test_results.py --limit 50         # Show more results
  python view_test_results.py --stats            # Show overall statistics
        """
    )
    
    parser.add_argument('--limit', type=int, default=20,
                        help='Number of results to display (default: 20)')
    parser.add_argument('--summary', action='store_true',
                        help='Show model performance summary')
    parser.add_argument('--detailed', action='store_true',
                        help='Show detailed results with full query text and responses')
    parser.add_argument('--model', type=str,
                        help='Filter results by specific model name')
    parser.add_argument('--stats', action='store_true',
                        help='Show overall test statistics')
    parser.add_argument('--list-models', action='store_true',
                        help='List available models')
    
    args = parser.parse_args()
    
    try:
        if args.list_models:
            print("🔍 Loading available models...")
            models = get_available_models()
            if models:
                print("\n📋 Available Models:")
                for i, model in enumerate(models, 1):
                    print(f"  {i}. {model}")
            else:
                print("❌ No models found")
            return
            
        if args.stats:
            print("🔍 Loading test statistics...")
            stats = get_test_statistics()
            if stats:
                print("\n📊 Overall Test Statistics:")
                print("=" * 50)
                print(f"Total Queries: {stats['total_queries']}")
                print(f"Models Tested: {stats['models_tested']}")
                print(f"Test Period: {stats['earliest_test']} to {stats['latest_test']}")
                print(f"\nAverage Metrics:")
                print(f"  • Factual Correctness: {stats['avg_factual_correctness']:.3f}" if stats['avg_factual_correctness'] else "  • Factual Correctness: N/A")
                print(f"  • Semantic Similarity: {stats['avg_semantic_similarity']:.3f}" if stats['avg_semantic_similarity'] else "  • Semantic Similarity: N/A")
                print(f"  • Context Recall: {stats['avg_context_recall']:.3f}" if stats['avg_context_recall'] else "  • Context Recall: N/A")
                print(f"  • Faithfulness: {stats['avg_faithfulness']:.3f}" if stats['avg_faithfulness'] else "  • Faithfulness: N/A")
            else:
                print("❌ No statistics found")
            return
        
        if args.summary:
            print("🔍 Loading model performance summary...")
            df = get_model_performance_summary()
            display_results_table(df, "Model Performance Summary")
            
        elif args.detailed:
            print("🔍 Loading detailed results...")
            df = get_detailed_results(args.limit)
            display_detailed_results(df)
            
        elif args.model:
            print(f"🔍 Loading results for model: {args.model}...")
            df = get_model_results(args.model, args.limit)
            if not df.empty:
                display_results_table(df, f"Results for {args.model}")
            else:
                print(f"❌ No results found for model: {args.model}")
                print("\n💡 Available models:")
                models = get_available_models()
                for model in models:
                    print(f"   • {model}")
            
        else:
            print("🔍 Loading recent test results...")
            df = get_recent_results(args.limit)
            display_results_table(df, "Recent Test Results")
            
            if not df.empty:
                # Show quick summary
                print(f"\n📈 Quick Summary:")
                print(f"   Models tested: {df['model_name'].nunique()}")
                
                # Calculate averages for non-null values
                numeric_cols = ['factual_correctness', 'semantic_similarity', 'context_recall', 'faithfulness']
                for col in numeric_cols:
                    if col in df.columns:
                        avg_val = df[col].mean()
                        if pd.notna(avg_val):
                            print(f"   Average {col.replace('_', ' ')}: {avg_val:.3f}")
                
                if 'timestamp' in df.columns:
                    print(f"   Time range: {df['timestamp'].min()} to {df['timestamp'].max()}")
        
        if not (args.summary or args.detailed or args.stats or args.list_models):
            print("\n💡 Tip: Use --detailed for full query text and responses")
            print("💡 Tip: Use --summary for model performance overview")
            print("💡 Tip: Use --stats for overall statistics")
            
    except Exception as e:
        print(f"❌ Error viewing results: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main() 