import logging
from flask_socketio import emit

class WebSocketLogHandler(logging.Handler):
    """Custom logging handler that emits logs to WebSocket clients"""
    
    def __init__(self, socket_event='log_message'):
        super().__init__()
        self.socket_event = socket_event
        
    def emit(self, record):
        try:
            log_entry = self.format(record)
            # Extract SQL query if present
            if "Running:" in log_entry:
                query = log_entry.split("Running:", 1)[1].strip()
                # Emit the SQL query to connected clients
                try:
                    emit(self.socket_event, {
                        'type': 'sql_query',
                        'content': query
                    }, namespace='/query', broadcast=True)
                except Exception as e:
                    # Log the error but don't crash
                    print(f"Error emitting websocket message: {e}")
        except Exception as e:
            print(f"Error in WebSocketLogHandler: {e}")
            self.handleError(record) 