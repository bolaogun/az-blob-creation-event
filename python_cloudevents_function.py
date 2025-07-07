import json
import logging
import azure.functions as func
from azure.messaging import CloudEvent
from typing import Dict, Any

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Function App configuration
app = func.FunctionApp()

@app.function_name(name="BlobCreatedHandler")
@app.event_grid_trigger(arg_name="event")
def blob_created_handler(event: func.EventGridEvent) -> None:
    """
    Azure Function that handles Blob Created events in CloudEvents v1.0 format.
    
    This function is triggered when a blob is created in the monitored storage account.
    It processes the CloudEvent and extracts relevant information about the blob.
    """
    
    try:
        # Log the raw event for debugging
        logger.info(f"Raw event received: {event}")
        
        # Extract CloudEvent data
        event_data = event.get_json()
        
        # Extract CloudEvent metadata
        event_info = {
            'id': event.id,
            'source': event.source,
            'subject': event.subject,
            'event_type': event.event_type,
            'event_time': event.event_time,
            'data_version': getattr(event, 'data_version', 'unknown')
        }
        
        logger.info(f"CloudEvent metadata: {json.dumps(event_info, indent=2, default=str)}")
        
        # Process the blob creation event
        if event_data:
            blob_info = extract_blob_info(event_data)
            process_blob_created(blob_info, event_info)
        else:
            logger.warning("No event data found in CloudEvent")
            
    except Exception as e:
        logger.error(f"Error processing CloudEvent: {str(e)}")
        raise

def extract_blob_info(event_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Extract blob information from the CloudEvent data.
    
    Args:
        event_data: The event data from the CloudEvent
        
    Returns:
        Dictionary containing blob information
    """
    try:
        blob_info = {
            'url': event_data.get('url', ''),
            'api': event_data.get('api', ''),
            'client_request_id': event_data.get('clientRequestId', ''),
            'request_id': event_data.get('requestId', ''),
            'etag': event_data.get('eTag', ''),
            'content_type': event_data.get('contentType', ''),
            'content_length': event_data.get('contentLength', 0),
            'blob_type': event_data.get('blobType', ''),
            'sequencer': event_data.get('sequencer', '')
        }
        
        # Extract blob name from URL
        if blob_info['url']:
            blob_info['blob_name'] = blob_info['url'].split('/')[-1]
            blob_info['container_name'] = blob_info['url'].split('/')[-2]
        
        return blob_info
        
    except Exception as e:
        logger.error(f"Error extracting blob info: {str(e)}")
        return {}

def process_blob_created(blob_info: Dict[str, Any], event_info: Dict[str, Any]) -> None:
    """
    Process the blob created event.
    
    Args:
        blob_info: Information about the created blob
        event_info: CloudEvent metadata
    """
    
    logger.info(f"Processing blob creation:")
    logger.info(f"  - Blob Name: {blob_info.get('blob_name', 'Unknown')}")
    logger.info(f"  - Container: {blob_info.get('container_name', 'Unknown')}")
    logger.info(f"  - Content Type: {blob_info.get('content_type', 'Unknown')}")
    logger.info(f"  - Content Length: {blob_info.get('content_length', 0)} bytes")
    logger.info(f"  - Event Time: {event_info.get('event_time', 'Unknown')}")
    
    # Example processing logic
    blob_name = blob_info.get('blob_name', '')
    content_type = blob_info.get('content_type', '')
    
    # Process different file types
    if content_type.startswith('image/'):
        process_image_blob(blob_info, event_info)
    elif content_type.startswith('text/'):
        process_text_blob(blob_info, event_info)
    elif content_type == 'application/json':
        process_json_blob(blob_info, event_info)
    else:
        process_generic_blob(blob_info, event_info)

def process_image_blob(blob_info: Dict[str, Any], event_info: Dict[str, Any]) -> None:
    """Process image blob creation."""
    logger.info(f"Processing image blob: {blob_info.get('blob_name')}")
    
    # Example: Trigger image processing pipeline
    # - Resize image
    # - Extract metadata
    # - Generate thumbnails
    # - Update database
    
    # Your image processing logic here
    pass

def process_text_blob(blob_info: Dict[str, Any], event_info: Dict[str, Any]) -> None:
    """Process text blob creation."""
    logger.info(f"Processing text blob: {blob_info.get('blob_name')}")
    
    # Example: Process text file
    # - Parse content
    # - Extract keywords
    # - Store in search index
    
    # Your text processing logic here
    pass

def process_json_blob(blob_info: Dict[str, Any], event_info: Dict[str, Any]) -> None:
    """Process JSON blob creation."""
    logger.info(f"Processing JSON blob: {blob_info.get('blob_name')}")
    
    # Example: Process JSON data
    # - Validate schema
    # - Transform data
    # - Store in database
    
    # Your JSON processing logic here
    pass

def process_generic_blob(blob_info: Dict[str, Any], event_info: Dict[str, Any]) -> None:
    """Process generic blob creation."""
    logger.info(f"Processing generic blob: {blob_info.get('blob_name')}")
    
    # Example: Generic processing
    # - Log event
    # - Send notification
    # - Update metadata
    
    # Your generic processing logic here
    pass

# Alternative HTTP trigger for CloudEvents (if EventGrid trigger doesn't work)
@app.function_name(name="BlobCreatedHttpHandler")
@app.route(route="cloudevents", auth_level=func.AuthLevel.ANONYMOUS, methods=["POST", "OPTIONS"])
def blob_created_http_handler(req: func.HttpRequest) -> func.HttpResponse:
    """
    Alternative HTTP trigger for handling CloudEvents v1.0.
    
    This function handles CloudEvent validation and event processing via HTTP.
    """
    
    try:
        # Handle validation request (OPTIONS method)
        if req.method == "OPTIONS":
            logger.info("Handling CloudEvent validation request")
            
            # Get the WebHook-Request-Origin header
            origin = req.headers.get("WebHook-Request-Origin")
            
            if origin:
                # Return the origin in the response header
                return func.HttpResponse(
                    status_code=200,
                    headers={"WebHook-Allowed-Origin": origin}
                )
            else:
                return func.HttpResponse(status_code=400)
        
        # Handle event data (POST method)
        elif req.method == "POST":
            logger.info("Processing CloudEvent via HTTP trigger")
            
            # Get the request body
            try:
                event_data = req.get_json()
                if not event_data:
                    logger.error("No JSON data in request")
                    return func.HttpResponse(status_code=400)
                
                # Process CloudEvent
                process_cloudevent_http(event_data)
                
                return func.HttpResponse(status_code=200)
                
            except Exception as e:
                logger.error(f"Error processing CloudEvent: {str(e)}")
                return func.HttpResponse(status_code=500)
        
        else:
            return func.HttpResponse(status_code=405)
            
    except Exception as e:
        logger.error(f"Error in HTTP CloudEvent handler: {str(e)}")
        return func.HttpResponse(status_code=500)

def process_cloudevent_http(event_data: Dict[str, Any]) -> None:
    """
    Process CloudEvent received via HTTP.
    
    Args:
        event_data: CloudEvent data
    """
    
    logger.info(f"CloudEvent received: {json.dumps(event_data, indent=2)}")
    
    # Extract CloudEvent fields
    spec_version = event_data.get('specversion', '1.0')
    event_type = event_data.get('type', '')
    source = event_data.get('source', '')
    event_id = event_data.get('id', '')
    subject = event_data.get('subject', '')
    time = event_data.get('time', '')
    data = event_data.get('data', {})
    
    logger.info(f"CloudEvent Details:")
    logger.info(f"  - Spec Version: {spec_version}")
    logger.info(f"  - Type: {event_type}")
    logger.info(f"  - Source: {source}")
    logger.info(f"  - ID: {event_id}")
    logger.info(f"  - Subject: {subject}")
    logger.info(f"  - Time: {time}")
    
    # Process based on event type
    if event_type == "Microsoft.Storage.BlobCreated":
        blob_info = extract_blob_info(data)
        event_info = {
            'id': event_id,
            'source': source,
            'subject': subject,
            'event_type': event_type,
            'event_time': time,
            'spec_version': spec_version
        }
        process_blob_created(blob_info, event_info)
    else:
        logger.warning(f"Unknown event type: {event_type}")

# Health check endpoint
@app.function_name(name="HealthCheck")
@app.route(route="health", auth_level=func.AuthLevel.ANONYMOUS)
def health_check(req: func.HttpRequest) -> func.HttpResponse:
    """Health check endpoint."""
    return func.HttpResponse(
        json.dumps({
            "status": "healthy",
            "timestamp": func.datetime.utcnow().isoformat(),
            "version": "1.0.0"
        }),
        status_code=200,
        headers={"Content-Type": "application/json"}
    )