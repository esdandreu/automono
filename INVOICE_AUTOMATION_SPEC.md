# Invoice Automation Workflow Specification

## Overview
This document specifies an automated invoice collection and management system that fetches invoices from multiple utility providers, stores them in cloud storage, and maintains a centralized record in Google Sheets.

## System Architecture

### Adapters and Ports Pattern
The system follows the **Adapters and Ports** (Hexagonal Architecture) pattern to ensure clean separation of concerns, easy testing, and maintainability. This allows the business logic to be completely isolated from external dependencies.

### Core Ports (Interfaces)

#### 1. Costs Source Port
**Purpose**: Abstract interface for iterating over invoices from various providers
```python
class CostsSource(ABC):
    @abstractmethod
    def __iter__(self) -> Iterator[Invoice]
```

**Note**: The iterator yields `Invoice` objects in chronological order from newest to oldest. Each adapter implementation handles all the complex navigation, authentication, and file retrieval internally. The business logic can break iteration when it encounters an already-registered invoice, making the process more efficient.

#### 2. Invoice Archive Port
**Purpose**: Abstract interface for storing invoice files in cloud storage
```python
class InvoiceArchive(ABC):
    @abstractmethod
    def archive_invoice(self, invoice: Invoice) -> ArchiveResult
    @abstractmethod
    def get_invoice_url(self, archive_id: str) -> str
```

#### 3. Costs Registry Port
**Purpose**: Abstract interface for managing invoice records and tracking
```python
class CostsRegistry(ABC):
    @abstractmethod
    def get_registered_invoices(self, since_date: datetime) -> List[RegisteredInvoice]
    @abstractmethod
    def register_invoice(self, invoice: Invoice, archive_results: List[ArchiveResult]) -> bool
```

### Adapters (Implementations)

#### Costs Source Adapters

##### Repsol Costs Source Adapter
- **Implementation**: `RepsolCostsSourceAdapter`
- **Technology**: Selenium WebDriver
- **Authentication**: Username/password form submission
- **Invoice Iteration**: Iterates over customer portal bills from newest to oldest
- **File Download**: Downloads each invoice PDF during iteration (handles all navigation internally)

##### Digi Costs Source Adapter
- **Implementation**: `DigiCostsSourceAdapter`
- **Technology**: Selenium WebDriver
- **Authentication**: Username/password form submission
- **Invoice Iteration**: Iterates over customer area invoices from newest to oldest
- **File Download**: Downloads each invoice PDF during iteration (handles all navigation internally)

##### Emivasa Costs Source Adapter
- **Implementation**: `EmivasaCostsSourceAdapter`
- **Technology**: Selenium WebDriver
- **Authentication**: Username/password form submission
- **Invoice Iteration**: Iterates over customer portal bills from newest to oldest
- **File Download**: Downloads each invoice PDF during iteration (handles all navigation internally)

#### Invoice Archive Adapters

##### Google Drive Archive Adapter
- **Implementation**: `GoogleDriveArchiveAdapter`
- **Technology**: Google Drive API v3
- **Authentication**: Service Account JSON credentials
- **Storage Structure**: `/Invoices/{Provider}/{Year}/{Month}/`
- **File Naming**: `{Provider}_{InvoiceNumber}_{Date}.pdf`

##### OneDrive Archive Adapter
- **Implementation**: `OneDriveArchiveAdapter`
- **Technology**: Microsoft Graph API
- **Authentication**: Azure App Registration
- **Storage Structure**: `/Invoices/{Provider}/{Year}/{Month}/`
- **File Naming**: `{Provider}_{InvoiceNumber}_{Date}.pdf`

##### Multiplexer Archive Adapter
- **Implementation**: `MultiplexerArchiveAdapter`
- **Purpose**: Stores invoices in both Google Drive and OneDrive
- **Strategy**: Parallel upload to both adapters
- **Error Handling**: Continues if one adapter fails, reports partial success
- **Result Aggregation**: Combines results from both storage adapters

#### Costs Registry Adapters

##### Google Sheets Costs Registry Adapter
- **Implementation**: `GoogleSheetsCostsRegistryAdapter`
- **Technology**: Google Sheets API v4
- **Authentication**: Service Account JSON credentials
- **Schema**: Invoice tracking and processing log sheets
- **Operations**: Read existing records, write new registrations

### Core Components
1. **Invoice Orchestrator**: Main use case that coordinates the workflow
2. **Browser Automation Service**: Shared Selenium service for web scraping
3. **File Processing Service**: Handles PDF validation and metadata extraction
4. **Idempotency Service**: Ensures no duplicate processing
5. **Error Handling Service**: Manages retries and error recovery
6. **Scheduler**: GitHub Actions workflow for automated execution

### Technology Stack
- **Language**: Python 3.11+
- **Architecture Pattern**: Adapters and Ports (Hexagonal Architecture)
- **Browser Automation**: Selenium WebDriver with Chrome (headless mode)
- **Cloud Storage**: Google Drive API, Microsoft Graph API (OneDrive)
- **Spreadsheet**: Google Sheets API
- **Scheduling**: GitHub Actions
- **Configuration**: Environment variables for credentials and settings
- **Testing**: pytest with extensive mocking capabilities

## Project Structure

```
src/
├── core/                            # Core business logic
│   ├── domain/                      # Domain models
│   │   ├── invoice_metadata.py
│   │   ├── invoice_file.py
│   │   ├── archive_result.py
│   │   └── registered_invoice.py
│   ├── ports/                       # Port interfaces
│   │   ├── costs_source.py
│   │   ├── invoice_archive.py
│   │   └── costs_registry.py
│   └── usecases/                    # Business logic use cases
│       ├── invoice_orchestrator.py
│       ├── idempotency_service.py
│       └── file_processing_service.py
├── adapters/                        # External integrations (adapters)
│   ├── costs_sources/               # Costs source adapters
│   │   ├── repsol/
│   │   │   ├── __init__.py
│   │   │   ├── repsol_costs_source_adapter.py
│   │   │   └── repsol_scraper.py
│   │   ├── digi/
│   │   │   ├── __init__.py
│   │   │   ├── digi_costs_source_adapter.py
│   │   │   └── digi_scraper.py
│   │   └── emivasa/
│   │       ├── __init__.py
│   │       ├── emivasa_costs_source_adapter.py
│   │       └── emivasa_scraper.py
│   ├── archives/                    # Archive adapters
│   │   ├── google_drive/
│   │   │   ├── __init__.py
│   │   │   └── google_drive_adapter.py
│   │   ├── onedrive/
│   │   │   ├── __init__.py
│   │   │   └── onedrive_adapter.py
│   │   └── multiplexer/
│   │       ├── __init__.py
│   │       └── multiplexer_adapter.py
│   └── registry/                    # Registry adapters
│       ├── google_sheets/
│       │   ├── __init__.py
│       │   └── google_sheets_costs_registry_adapter.py
├── infrastructure/                  # Infrastructure services
│   ├── browser/
│   │   ├── __init__.py
│   │   └── selenium_service.py
│   ├── config/
│   │   ├── __init__.py
│   │   └── settings.py
│   └── logging/
│       ├── __init__.py
│       └── logger.py
├── main.py                          # Application entry point
└── __init__.py

tests/
├── unit/                            # Unit tests
│   ├── core/                        # Business logic tests
│   ├── adapters/                    # Adapter tests with mocks
│   └── infrastructure/              # Infrastructure tests
├── integration/                     # Integration tests
│   ├── adapters/                    # Real adapter tests
│   └── end_to_end/                  # Full workflow tests
├── fixtures/                        # Test data and fixtures
└── mocks/                           # Mock implementations

.github/
└── workflows/
    └── invoice_automation.yml       # GitHub Actions workflow
```

## Invoice Sources

### 1. Repsol (Electricity Bills)
- **URL**: https://www.repsol.es/
- **Authentication**: Username/password login
- **Invoice Location**: Customer portal → Bills section
- **File Format**: PDF
- **Frequency**: Monthly

### 2. Digi (Internet Bills)
- **URL**: https://www.digi.es/
- **Authentication**: Username/password login
- **Invoice Location**: Customer area → Invoices
- **File Format**: PDF
- **Frequency**: Monthly

### 3. Emivasa (Water Bills)
- **URL**: https://www.emivasa.es/
- **Authentication**: Username/password login
- **Invoice Location**: Customer portal → Bills
- **File Format**: PDF
- **Frequency**: Bi-monthly

## Data Models

### Core Domain Models

#### Invoice
```python
@dataclass
class Invoice:
    # Metadata fields
    invoice_date: datetime  # Extracted from invoice document
    concept: str  # Provider-specific parameter (e.g., "Electricity", "Internet", "Water")
    type: str  # Provider-specific parameter (e.g., "Monthly Bill", "Quarterly Bill")
    cost_euros: Decimal  # Extracted from invoice document
    iva_euros: Decimal  # Extracted from invoice document (VAT amount)
    deductible_percentage: float  # Provider-specific parameter (e.g., 0.0, 0.5, 1.0)
    file_name: str
    
    # File fields
    content: bytes
    content_type: str
    size: int
    hash_md5: str
    hash_sha256: str
```

#### ArchiveResult
```python
@dataclass
class ArchiveResult:
    archive_id: str
    archive_type: str  # "google_drive", "onedrive"
    file_url: str
    success: bool
    error_message: Optional[str] = None
```

#### RegisteredInvoice
```python
@dataclass
class RegisteredInvoice:
    invoice_date: datetime
    concept: str
    type: str
    cost_euros: Decimal
    iva_euros: Decimal
    deductible_percentage: float
    file_hash: str
    google_drive_id: Optional[str]
    onedrive_id: Optional[str]
    processed_date: datetime
    status: str  # "success", "failed", "skipped"
```

## Data Extraction Strategy

### Provider-Specific Parameters
These parameters are configured per provider and don't change between invoices:

- **concept**: Fixed concept for each provider
  - Repsol: "Electricity"
  - Digi: "Internet" 
  - Emivasa: "Water"
- **type**: Fixed type for each provider
  - Repsol: "Monthly Bill"
  - Digi: "Monthly Bill"
  - Emivasa: "Bi-monthly Bill"
- **deductible_percentage**: Fixed percentage for each provider
  - Repsol: 1.0 (100% deductible for business)
  - Digi: 1.0 (100% deductible for business)
  - Emivasa: 0.0 (0% deductible - personal expense)

### Invoice Document Extraction
These fields are extracted from the actual invoice PDF using OCR or text parsing:

- **invoice_date**: Date when the invoice was issued
- **cost_euros**: Base cost amount in euros (before VAT)
- **iva_euros**: VAT amount in euros

## Data Flow

```
1. GitHub Actions Trigger (Scheduled)
   ↓
2. Invoice Orchestrator Initialization
   ↓
3. For each provider (Repsol, Digi, Emivasa):
   a. Create CostsSource adapter with provider-specific parameters
   b. Authenticate with provider portal
   c. Iterate over invoices (newest to oldest):
      - For each Invoice object from CostsSource iterator:
        - Check if already registered (CostsRegistry)
        - If already registered: break iteration (stop processing older invoices)
        - If not registered:
          - Store in both archives (MultiplexerArchiveAdapter)
          - Register complete invoice (CostsRegistry)
   ↓
4. Generate execution report
   ↓
5. Send notifications (if configured)
```

## Idempotency Strategy

### Invoice Identification
- **Primary Key**: Invoice Date + Concept + Type + Cost Amount
- **Secondary Key**: File hash (MD5/SHA256) for duplicate detection
- **Storage**: Google Sheets maintains processing history

### Duplicate Prevention
1. **Pre-processing Check**: Query Google Sheets for existing records
2. **File Hash Verification**: Compare downloaded file against stored hashes
3. **Date Range Filtering**: Only process invoices from last 3 months
4. **Skip Logic**: If invoice already processed, skip download and upload

### State Management
- **Processing Log**: Detailed log of each execution
- **Error Recovery**: Resume from last successful operation
- **Retry Logic**: Exponential backoff for transient failures

## Google Sheets Schema

### Invoice Tracking Sheet
| Column | Type | Description |
|--------|------|-------------|
| invoice_date | Date | Date of the invoice |
| concept | String | Invoice concept (Electricity, Internet, Water) |
| type | String | Invoice type (Monthly Bill, Quarterly Bill) |
| cost_euros | Number | Invoice cost in euros |
| iva_euros | Number | VAT amount in euros |
| deductible_percentage | Number | Deductible percentage (0.0-1.0) |
| file_hash | String | MD5 hash of the PDF file |
| google_drive_id | String | Google Drive file ID |
| onedrive_id | String | OneDrive file ID |
| processed_date | DateTime | When the invoice was processed |
| status | String | Success, Failed, Skipped |

### Processing Log Sheet
| Column | Type | Description |
|--------|------|-------------|
| execution_id | String | Unique execution identifier |
| start_time | DateTime | Execution start time |
| end_time | DateTime | Execution end time |
| provider | String | Provider being processed |
| status | String | Success, Failed, Partial |
| invoices_processed | Number | Count of invoices processed |
| errors | String | Error details (if any) |

## Environment Configuration

### Required Environment Variables
```bash
# Provider Credentials
REPSOL_USERNAME=your_repsol_username
REPSOL_PASSWORD=your_repsol_password
DIGI_USERNAME=your_digi_username
DIGI_PASSWORD=your_digi_password
EMIVASA_USERNAME=your_emivasa_username
EMIVASA_PASSWORD=your_emivasa_password

# Google Services
GOOGLE_CREDENTIALS_JSON=base64_encoded_service_account_json
GOOGLE_SHEETS_ID=your_google_sheets_id
GOOGLE_DRIVE_FOLDER_ID=your_drive_folder_id

# Microsoft Services
MICROSOFT_CLIENT_ID=your_azure_app_client_id
MICROSOFT_CLIENT_SECRET=your_azure_app_secret
MICROSOFT_TENANT_ID=your_azure_tenant_id
ONEDRIVE_FOLDER_ID=your_onedrive_folder_id

# Application Settings
HEADLESS_MODE=true
DOWNLOAD_TIMEOUT=300
MAX_RETRIES=3
LOG_LEVEL=INFO
```

## Browser Automation Requirements

### Selenium Configuration
- **Browser**: Chrome (headless mode for GitHub Actions)
- **Window Size**: 1920x1080 (for consistent rendering)
- **User Agent**: Standard Chrome user agent
- **Download Directory**: Temporary directory for invoice files
- **Implicit Wait**: 10 seconds for element loading
- **Page Load Timeout**: 30 seconds

### Authentication Flow
1. Navigate to provider login page
2. Fill username and password fields
3. Submit login form
4. Wait for successful authentication
5. Navigate to invoices section
6. Handle any 2FA if required (future enhancement)

### Error Handling
- **Login Failures**: Retry with exponential backoff
- **Network Timeouts**: Retry up to MAX_RETRIES times
- **Element Not Found**: Log error and continue with next provider
- **Download Failures**: Mark invoice as failed and continue

## Cloud Storage Integration

### Google Drive
- **API**: Google Drive API v3
- **Authentication**: Service Account with JSON credentials
- **Folder Structure**: `/Invoices/{Provider}/{Year}/{Month}/`
- **File Naming**: `{Provider}_{InvoiceNumber}_{Date}.pdf`
- **Permissions**: Service account has write access to designated folder

### OneDrive
- **API**: Microsoft Graph API
- **Authentication**: Azure App Registration with client credentials
- **Folder Structure**: `/Invoices/{Provider}/{Year}/{Month}/`
- **File Naming**: `{Provider}_{InvoiceNumber}_{Date}.pdf`
- **Permissions**: App has write access to designated folder

## GitHub Actions Workflow

### Schedule
```yaml
on:
  schedule:
    # Run every Monday at 9:00 AM UTC
    - cron: '0 9 * * 1'
  workflow_dispatch: # Allow manual execution
```

### Environment Setup
- **OS**: ubuntu-latest
- **Python**: 3.11
- **Chrome**: Latest stable version
- **ChromeDriver**: Matching version

### Workflow Steps
1. **Checkout Code**: Get latest version of the automation script
2. **Setup Python**: Install Python and dependencies
3. **Setup Chrome**: Install Chrome and ChromeDriver
4. **Install Dependencies**: pip install requirements.txt
5. **Run Automation**: Execute the main Python script
6. **Upload Logs**: Store execution logs as artifacts
7. **Send Notifications**: Email/Slack notification on completion

## Error Handling and Monitoring

### Error Categories
1. **Authentication Errors**: Invalid credentials, account locked
2. **Network Errors**: Timeout, connection refused, DNS issues
3. **Parsing Errors**: Website structure changes, missing elements
4. **Storage Errors**: API quota exceeded, permission denied
5. **System Errors**: Out of memory, disk space, Chrome crashes

### Monitoring and Alerting
- **Success Rate**: Track percentage of successful executions
- **Processing Time**: Monitor execution duration
- **Error Frequency**: Alert on repeated failures
- **Storage Usage**: Monitor cloud storage consumption

### Logging Strategy
- **Structured Logging**: JSON format for easy parsing
- **Log Levels**: DEBUG, INFO, WARNING, ERROR, CRITICAL
- **Log Retention**: 30 days for INFO+, 7 days for DEBUG
- **Log Storage**: GitHub Actions artifacts + optional external service

## Security Considerations

### Credential Management
- **Environment Variables**: All credentials stored as GitHub Secrets
- **Service Accounts**: Limited permissions for cloud services
- **Credential Rotation**: Regular rotation of API keys and passwords
- **Audit Logging**: Track all credential usage

### Data Protection
- **File Encryption**: PDFs encrypted in transit and at rest
- **Access Control**: Principle of least privilege for all services
- **Data Retention**: Automatic cleanup of temporary files
- **Privacy**: No sensitive data in logs or error messages

## Testing Strategy

### Architecture Benefits for Testing
The Adapters and Ports pattern enables comprehensive testing by allowing complete isolation of business logic from external dependencies through dependency injection and interface mocking.

### Unit Tests

#### Business Logic Tests (Core Domain)
- **Invoice Orchestrator**: Test main workflow use case with mocked adapters
- **Idempotency Service**: Test duplicate detection and prevention logic
- **File Processing Service**: Test PDF validation and metadata extraction
- **Domain Models**: Test data validation and business rules

#### Adapter Tests (Isolated)
- **Invoice Source Adapters**: Test individual provider scrapers with mocked web responses
- **Archive Adapters**: Test Google Drive and OneDrive integrations with mocked APIs
- **Registry Adapters**: Test Google Sheets integration with mocked API responses
- **Multiplexer Adapter**: Test parallel upload logic and error handling

### Integration Tests

#### Adapter Integration Tests
- **Real API Tests**: Test adapters against actual cloud service APIs (with test data)
- **Browser Automation Tests**: Test Selenium adapters with mock websites
- **End-to-End Adapter Tests**: Test complete adapter workflows with test accounts

#### System Integration Tests
- **Complete Workflow**: Test full system with test accounts and test storage
- **Error Scenarios**: Test system behavior under various failure conditions
- **Performance Tests**: Test system performance with large numbers of invoices

### Test Doubles and Mocking

#### Mock Adapters
```python
class MockCostsSource(CostsSource):
    def __iter__(self) -> Iterator[Invoice]:
        # Yield predefined test Invoice objects from newest to oldest
        for invoice in self.test_invoices:
            yield invoice

class MockInvoiceArchive(InvoiceArchive):
    def archive_invoice(self, invoice: Invoice) -> ArchiveResult:
        # Simulate successful storage
        pass
```

#### Test Data Factories
```python
class InvoiceFactory:
    @staticmethod
    def create_repsol_invoice() -> Invoice:
        # Create test Repsol invoice with metadata and file content
        pass
    
    @staticmethod
    def create_digi_invoice() -> Invoice:
        # Create test Digi invoice with metadata and file content
        pass
```

### Test Environment
- **Test Credentials**: Separate test accounts for each provider
- **Test Storage**: Dedicated test folders in cloud storage
- **Test Spreadsheet**: Separate Google Sheet for testing
- **Mock Services**: Local mock services for external APIs during development

### Test Categories

#### Fast Tests (Unit Tests)
- **Business Logic**: All core domain logic
- **Adapters**: Individual adapter functionality with mocks
- **Utilities**: Helper functions and data processing
- **Target**: < 1 second per test, run on every commit

#### Medium Tests (Integration Tests)
- **Adapter Integration**: Real API calls with test data
- **Browser Automation**: Selenium tests with mock websites
- **Target**: < 30 seconds per test, run on pull requests

#### Slow Tests (End-to-End Tests)
- **Complete Workflow**: Full system tests with real services
- **Performance Tests**: Load and stress testing
- **Target**: < 5 minutes per test, run on main branch

### Test Coverage Requirements
- **Business Logic**: 100% line coverage
- **Adapters**: 90% line coverage
- **Error Handling**: 100% coverage of error paths
- **Integration Points**: 80% coverage of API interactions

## Deployment and Maintenance

### Version Control
- **Git Flow**: Feature branches, pull requests, semantic versioning
- **Release Tags**: Tagged releases for production deployments
- **Change Log**: Maintain detailed change log for each release

### Monitoring and Maintenance
- **Health Checks**: Regular validation of all integrations
- **Dependency Updates**: Monthly updates of Python packages
- **Browser Updates**: Automatic Chrome/ChromeDriver updates
- **Performance Monitoring**: Track execution times and resource usage

---

*This specification serves as the foundation for the invoice automation system. It should be reviewed and updated as requirements evolve and new features are added.*
