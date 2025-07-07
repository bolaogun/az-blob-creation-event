# Azure Functions CloudEvents Deployment with Terraform

This solution deploys an Azure Function that responds to Azure Storage Blob Created events using CloudEvents v1.0 schema. The function code is retrieved from a GitLab package registry and deployed to Azure using Terraform.

## Architecture Overview

- **Azure Function App**: Python-based function that handles CloudEvents v1.0
- **Azure Storage Account**: Monitored for blob creation events
- **Azure Event Grid**: Routes blob events to the function using CloudEvents schema
- **GitLab Package Registry**: Source for the function deployment package
- **Application Insights**: Monitoring and logging

## Prerequisites

1. **Azure CLI** installed and configured
2. **Terraform** v1.0 or later
3. **Azure subscription** with appropriate permissions
4. **GitLab access token** with package registry read permissions
5. **Python function package** stored in GitLab package registry as a .zip file

## GitLab Package Registry Setup

Your Python function package should be uploaded to GitLab's package registry. The package should contain:

```
function-package.zip
├── function_app.py          # Main function code
├── requirements.txt         # Python dependencies
├── host.json               # Function host configuration
└── .funcignore             # Files to ignore (optional)
```

### Upload Package to GitLab

```bash
# Example: Upload package to GitLab
curl --header "PRIVATE-TOKEN: $GITLAB_TOKEN" \
     --upload-file function-package.zip \
     "https://gitlab.com/api/v4/projects/$PROJECT_ID/packages/generic/my-function-package/1.0.0/my-function-package.zip"
```

## Terraform Configuration

### 1. Create terraform.tfvars

Create a `terraform.tfvars` file with your specific values:

```hcl
# GitLab Configuration
gitlab_access_token = "your-gitlab-access-token"
gitlab_project_id = "12345"
gitlab_package_name = "my-function-package"
gitlab_package_version = "1.0.0"
gitlab_base_url = "https://gitlab.com"  # Optional, defaults to gitlab.com

# Azure Configuration
function_app_name = "my-cloudevents-function"
storage_account_name = "mystorageaccount001"
blob_storage_account_name = "myblobstorage001"
blob_container_name = "monitored-container"
```

### 2. Initialize and Deploy

```bash
# Initialize Terraform
terraform init

# Plan the deployment
terraform plan

# Deploy the infrastructure
terraform apply
```

## Function Configuration

The deployed function includes:

### CloudEvents v1.0 Support

- **EventGrid Trigger**: Primary trigger for CloudEvents
- **HTTP Trigger**: Alternative endpoint for CloudEvents validation
- **Schema Validation**: Handles CloudEvents v1.0 specification
- **Blob Processing**: Extracts and processes blob creation events

### Event Processing

The function processes different blob types:

- **Image files**: Trigger image processing pipeline
- **Text files**: Parse and index content
- **JSON files**: Validate and transform data
- **Generic files**: Log and notify

## CloudEvents Schema

The function handles CloudEvents v1.0 with the following structure:

```json
{
  "specversion": "1.0",
  "type": "Microsoft.Storage.BlobCreated",
  "source": "/subscriptions/{subscription}/resourceGroups/{rg}/providers/Microsoft.Storage/storageAccounts/{account}",
  "id": "unique-event-id",
  "time": "2025-01-01T12:00:00Z",
  "subject": "/blobServices/default/containers/monitored-container/blobs/example.txt",
  "datacontenttype": "application/json",
  "data": {
    "api": "PutBlob",
    "clientRequestId": "client-request-id",
    "requestId": "request-id",
    "eTag": "blob-etag",
    "contentType": "application/octet-stream",
    "contentLength": 1024,
    "blobType": "BlockBlob",
    "url": "https://account.blob.core.windows.net/container/blob.txt",
    "sequencer": "sequence-number"
  }
}
```

## Testing the Deployment

### 1. Verify Function Deployment

```bash
# Check function app status
az functionapp show --name $FUNCTION_APP_NAME --resource-group $RESOURCE_GROUP_NAME

# Check function logs
az functionapp logs tail --name $FUNCTION_APP_NAME --resource-group $RESOURCE_GROUP_NAME
```

### 2. Test Blob Creation Event

```bash
# Upload a test file to trigger the event
az storage blob upload \
  --account-name $BLOB_STORAGE_ACCOUNT_NAME \
  --container-name $BLOB_CONTAINER_NAME \
  --name test-file.txt \
  --file local-test-file.txt
```

### 3. Monitor Function Execution

- **Application Insights**: View telemetry and logs
- **Azure Portal**: Monitor function executions
- **Function Logs**: Check real-time execution logs

## Troubleshooting

### Common Issues

1. **GitLab Package Not Found**
   - Verify access token permissions
   - Check project ID and package name
   - Ensure package version exists

2. **Function Not Triggering**
   - Verify Event Grid subscription is active
   - Check blob container name matches configuration
   - Ensure function app is running

3. **CloudEvents Validation Issues**
   - Verify Event Grid uses CloudEvents v1.0 schema
   - Check function endpoint URL
   - Ensure proper CORS configuration

### Debugging Steps

```bash
# Check Event Grid subscription
az eventgrid event-subscription show \
  --name blob-created-subscription \
  --source-resource-id /subscriptions/.../storageAccounts/...

# View function app settings
az functionapp config appsettings list \
  --name $FUNCTION_APP_NAME \
  --resource-group $RESOURCE_GROUP_NAME

# Check function app logs
az functionapp logs tail \
  --name $FUNCTION_APP_NAME \
  --resource-group $RESOURCE_GROUP_NAME
```

## Package Update Process

To update the function code:

1. **Upload New Package Version**
   ```bash
   curl --header "PRIVATE-TOKEN: $GITLAB_TOKEN" \
        --upload-file function-package-v2.zip \
        "https://gitlab.com/api/v4/projects/$PROJECT_ID/packages/generic/my-function-package/2.0.0/my-function-package.zip"
   ```

2. **Update Terraform Variables**
   ```hcl
   gitlab_package_version = "2.0.0"
   ```

3. **Apply Changes**
   ```bash
   terraform apply
   ```

The function app will automatically restart with the new package due to the `PACKAGE_HASH` app setting change.

## Security Considerations

### Access Control
- GitLab access token should have minimal required permissions
- Use Azure Key Vault for sensitive configuration values
- Enable managed identity for Azure resource access

### Network Security
- Consider using private endpoints for storage accounts
- Implement proper CORS policies
- Use HTTPS only for all endpoints

### Monitoring
- Enable Application Insights for comprehensive monitoring
- Set up alerts for function failures
- Monitor Event Grid delivery failures

## Advanced Configuration

### Custom Event Filters

Add advanced filters to the Event Grid subscription:

```hcl
# In the azurerm_eventgrid_event_subscription resource
advanced_filter {
  string_begins_with {
    key    = "data.contentType"
    values = ["image/", "application/json"]
  }
}

advanced_filter {
  number_greater_than {
    key   = "data.contentLength"
    value = 1024
  }
}
```

### Function Scaling

For high-volume scenarios, consider:

```hcl
# Use Premium plan for better performance
resource "azurerm_service_plan" "main" {
  name                = "asp-${var.function_app_name}"
  resource_group_name = azurerm_resource_group.main.name
  location            = azurerm_resource_group.main.location
  os_type             = "Linux"
  sku_name            = "EP1"  # Premium plan
}
```

### Multiple Environment Support

Create environment-specific configurations:

```bash
# Development
terraform workspace new dev
terraform apply -var-file="dev.tfvars"

# Production
terraform workspace new prod
terraform apply -var-file="prod.tfvars"
```

## Cleanup

To remove all resources:

```bash
# Destroy all resources
terraform destroy

# Remove workspace (optional)
terraform workspace delete dev
```

## Additional Resources

- [Azure Functions Python Developer Guide](https://docs.microsoft.com/en-us/azure/azure-functions/functions-reference-python)
- [CloudEvents v1.0 Specification](https://cloudevents.io/)
- [Azure Event Grid CloudEvents Schema](https://docs.microsoft.com/en-us/azure/event-grid/cloud-event-schema)
- [GitLab Package Registry API](https://docs.gitlab.com/ee/api/packages.html)

## Support

For issues and questions:
- Check the troubleshooting section above
- Review Azure Functions logs in Application Insights
- Verify Event Grid subscription status
- Ensure GitLab package registry access
    