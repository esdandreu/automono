# Invoice Automation System

An automated invoice collection and management system that fetches invoices from multiple utility providers, stores them in cloud storage, and maintains a centralized record in Google Sheets.

## Architecture

This system follows the **Adapters and Ports** (Hexagonal Architecture) pattern to ensure clean separation of concerns, easy testing, and maintainability.

### Core Components

- **Domain Models**: Core business entities (`InvoiceMetadata`, `InvoiceFile`, `ArchiveResult`, `RegisteredInvoice`)
- **Ports**: Abstract interfaces defining contracts (`CostsSource`, `InvoiceArchive`, `CostsRegistry`)
- **Use Cases**: Business logic services (`InvoiceOrchestrator`, `IdempotencyService`, `FileProcessingService`)
- **Adapters**: External integrations (to be implemented)
- **Infrastructure**: Shared services (browser automation, configuration, logging)

## Current Status

### ✅ Implemented

- **Project Structure**: Complete directory structure following Clean Architecture
- **Domain Models**: All core domain models with validation
- **Port Interfaces**: Abstract interfaces for all external dependencies
- **Core Use Cases**: Main business logic services
- **Infrastructure**: Configuration, logging, and browser automation services
- **Main Entry Point**: Application orchestrator
- **Costs Source Adapters**: 
  - ✅ Repsol costs source adapter (Electricity)
  - ✅ Digi costs source adapter (Internet)
  - ✅ Emivasa costs source adapter (Water)
- **Testing**: Unit tests for domain models and adapters

### 🚧 To Be Implemented

- **Archive Adapters**:
  - Google Drive archive adapter
  - OneDrive archive adapter
  - Multiplexer archive adapter
- **Registry Adapter**:
  - Google Sheets costs registry adapter
- **GitHub Actions Workflow**: Scheduled execution

## Getting Started

### Prerequisites

- Python 3.11+
- Chrome browser (for Selenium)
- Google Cloud service account credentials
- Microsoft Azure app registration
- Provider account credentials (Repsol, Digi, Emivasa)

### Installation

1. Clone the repository:
```bash
git clone https://github.com/esdandreu/automono.git
cd automono
```

2. Create a virtual environment:
Unix:
```bash
python -m venv venv
source venv/bin/activate 
```

Windows:
```powershell
python -m venv venv
venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Set up environment variables (create `.env` file):
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

### Running the System

The system can now fetch invoices from all three providers but will show a warning that archive and registry adapters need to be implemented:

```bash
python src/main.py
```

**Current Capabilities:**
- ✅ Can authenticate with Repsol, Digi, and Emivasa portals
- ✅ Can extract invoice metadata from provider websites
- ✅ Can download invoice PDF files
- ✅ Can process and validate PDF files
- 🚧 Cannot store files in cloud storage yet
- 🚧 Cannot track processed invoices yet

### Running Tests

```bash
pytest tests/ -v
```

### Type Checking

The codebase uses comprehensive type annotations for better IDE support and static analysis:

```bash
# Run type checking with mypy
python type_check.py

# Or directly with mypy
mypy --strict src/
```

### Type Safety Features

- **Protocol-based interfaces**: Using `typing.Protocol` for better duck typing
- **Literal types**: For status values and other constrained types
- **Final annotations**: For constants and immutable values
- **Comprehensive type hints**: All functions and methods are fully typed
- **Runtime type validation**: Domain models validate types at runtime

Example:
```python
from src.core.domain.registered_invoice import InvoiceStatus

# Type-safe status assignment
status: InvoiceStatus = "success"  # ✅ Valid
status = "invalid"  # ❌ Type error
```

## Invoice Data Model

The system processes invoices with the following structure:

- **invoice_date**: Date when the invoice was issued (extracted from PDF)
- **concept**: Invoice concept (Electricity, Internet, Water)
- **type**: Invoice type (Monthly Bill, Bi-monthly Bill)
- **cost_euros**: Base cost amount in euros (extracted from PDF)
- **iva_euros**: VAT amount in euros (extracted from PDF)
- **deductible_percentage**: Deductible percentage (0.0-1.0)

## Provider Configuration

Each provider has fixed parameters:

- **Repsol**: Electricity, Monthly Bill, 100% deductible
- **Digi**: Internet, Monthly Bill, 100% deductible  
- **Emivasa**: Water, Bi-monthly Bill, 0% deductible

## Next Steps

1. Implement the costs source adapters for each provider
2. Implement the archive adapters for Google Drive and OneDrive
3. Implement the Google Sheets registry adapter
4. Set up GitHub Actions workflow for scheduled execution
5. Add comprehensive integration tests
6. Deploy and configure the system

## Development

The codebase follows these principles:

- **Clean Architecture**: Clear separation between business logic and external dependencies
- **Testability**: All business logic can be tested with mocked adapters
- **Maintainability**: Each provider can be updated independently
- **Extensibility**: New providers or storage services can be added easily
- **Error Handling**: Comprehensive error handling and logging throughout

## License

See LICENSE file for details.