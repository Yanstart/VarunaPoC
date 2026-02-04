---
name: api-documenter
description: Document FastAPI endpoints following API Documentation Protocol from CLAUDE.md. Ensures comprehensive docstrings, tags, parameter descriptions, and Swagger UI integration.
allowed-tools: Read, Write, Edit, Glob, Grep
---

# API Documenter Skill

This skill automates the creation of comprehensive FastAPI endpoint documentation following the **API Documentation Protocol** defined in `CLAUDE.md`.

## When to Use This Skill

Invoke this skill when:

- ✅ Creating a new API endpoint
- ✅ Modifying an existing endpoint (new parameters, changed behavior)
- ✅ Changing response structure
- ✅ Adding new error codes

## What This Skill Does

1. **Validates endpoint documentation** (docstring, tags, parameters)
2. **Ensures FastAPI best practices** (Query(), Path(), proper typing)
3. **Checks tag assignment** (health, navigation, visualization, etc.)
4. **Verifies Swagger UI** integration
5. **Updates main.py** if new tags are added
6. **Generates complete docstring** with all required sections

## FastAPI Documentation Requirements

Every endpoint MUST have:

### 1. Complete Docstring

```python
@router.get("/endpoint", tags=["category"])
async def endpoint_name(
    param1: str = Query(..., description="Parameter description"),
    param2: int = Query(default=10, ge=1, le=100, description="Range 1-100")
):
    """
    Brief one-line description of endpoint.

    Detailed explanation if needed (multiple lines).
    Explain use case, behavior, etc.

    Args:
        param1: Type and description
        param2: Type, default value, constraints, description

    Returns:
        Response structure:
        ```json
        {
            "field1": "type and description",
            "field2": 123,
            "nested": {
                "subfield": "description"
            }
        }
        ```

    Raises:
        400: Description of Bad Request error
        404: Description of Not Found error
        500: Description of server error

    Technical Notes:
        - Implementation details
        - Performance considerations
        - Dependencies (OpenSlide, filesystem, etc.)
        - Known limitations

    Examples:
        ```
        GET /api/endpoint?param1=value&param2=20

        Response:
        {
            "field1": "example",
            "field2": 20
        }
        ```
    """
    # Implementation
    pass
```

### 2. Appropriate Tag

Available tags (defined in `main.py`):

- **`health`** - Health check endpoints (`/`, `/api/health`)
- **`navigation`** - Navigation and slide detection (`/api/slides/browse`)
- **`visualization`** - Slide viewing and rendering (`/api/slides/{id}/info`, tiles)

**If new category needed:** Update `openapi_tags` in `main.py`:
```python
openapi_tags = [
    ...,
    {
        "name": "new_category",
        "description": "Description of new category"
    }
]
```

### 3. Documented Parameters

Use FastAPI `Query()` and `Path()` for parameter documentation:

```python
from fastapi import Query, Path

async def endpoint(
    slide_id: str = Path(..., description="Unique slide ID (MD5 hash)"),
    level: int = Path(..., ge=0, description="Pyramid level (0=highest resolution)"),
    limit: int = Query(default=20, ge=1, le=100, description="Results per page (1-100)"),
    offset: int = Query(default=0, ge=0, description="Skip first N results")
):
    pass
```

**Parameter validation:**
- `...` → Required parameter
- `default=X` → Optional with default value
- `ge=X` → Greater or equal (≥)
- `le=X` → Less or equal (≤)
- `gt=X` → Greater than (>)
- `lt=X` → Less than (<)
- `min_length`, `max_length` → String length
- `regex` → Pattern validation

## Docstring Template

Use this template for all endpoints:

```python
def endpoint_name(params):
    """
    [One-line summary]

    [Detailed description - optional, use if complex endpoint]

    Args:
        param1: [Type] - [Description with constraints]
        param2: [Type] - [Description with default value]

    Returns:
        [Response structure with JSON example]
        Include all fields with types and descriptions

    Raises:
        400: [When and why Bad Request]
        404: [When and why Not Found]
        500: [When and why Internal Server Error]
        [Add other status codes as needed]

    Technical Notes:
        - [Implementation detail 1]
        - [Performance consideration]
        - [Dependency note]
        - [Known limitation]

    Security:
        [If applicable: authentication, authorization, data protection]

    Examples:
        ```
        [HTTP method] [endpoint URL with example params]

        Response:
        [JSON response example]
        ```
    """
```

## Example Endpoints

### Example 1: Navigation Endpoint

```python
@router.get("/browse", tags=["navigation"])
async def browse_slides_directory(
    path: str = Query("/", description="Relative path from /Slides root")
):
    """
    Browse slides directory hierarchically.

    Navigate folder by folder (non-recursive) through the slide directory tree.
    Returns folders, detected slides, and unsupported files for the specified path.

    Args:
        path: Relative path from /Slides root
              Examples: "/", "/3DHistech", "/projects/2024"

    Returns:
        Navigation data structure:
        ```json
        {
            "current_path": "/3DHistech",
            "parent_path": "/",
            "breadcrumb": ["/", "3DHistech"],
            "folders": [
                {"name": "subfolder", "path": "/3DHistech/subfolder", "item_count": 5}
            ],
            "slides": [
                {
                    "name": "sample.mrxs",
                    "id": "abc123...",
                    "format_string": "3DHISTECH MIRAX",
                    "dimensions": [100000, 80000],
                    "level_count": 9
                }
            ],
            "files": [
                {"name": "readme.txt", "extension": ".txt", "notes": "Not a slide"}
            ]
        }
        ```

    Raises:
        400: Path traversal attempt detected (../ blocked)
        404: Directory not found
        500: Error browsing directory (permissions, I/O error)

    Security:
        - Path traversal blocked (../ forbidden)
        - Access restricted to /Slides root only
        - No sensitive information in error messages

    Technical Notes:
        - Non-recursive (single level depth)
        - Uses format_detector to identify slides
        - Files without extension marked unsupported
        - See docs/Manuel/02-NAVIGATION_DOSSIERS.md for user guide

    Examples:
        ```
        GET /api/slides/browse?path=/3DHistech

        Response:
        {
            "current_path": "/3DHistech",
            "parent_path": "/",
            "folders": [...],
            "slides": [...]
        }
        ```
    """
    # Implementation
    pass
```

### Example 2: Visualization Endpoint

```python
@router.get("/{slide_id}/info", tags=["visualization"])
async def get_slide_info(
    slide_id: str = Path(..., description="Unique slide ID (MD5 hash of file path)")
):
    """
    Retrieve slide metadata.

    Opens slide temporarily with OpenSlide to extract dimensions,
    pyramid levels, vendor information, and other properties.
    Closes immediately after extraction.

    Args:
        slide_id: Unique slide identifier (MD5 hash)

    Returns:
        Slide metadata:
        ```json
        {
            "dimensions": [100000, 80000],
            "level_count": 9,
            "level_dimensions": [[100000, 80000], [50000, 40000], ...],
            "level_downsamples": [1.0, 2.0, 4.0, ...],
            "vendor": "3DHISTECH",
            "format": "mirax",
            "properties": {
                "openslide.objective-power": "20",
                "openslide.mpp-x": "0.5",
                "openslide.mpp-y": "0.5"
            }
        }
        ```

    Raises:
        404: Slide not found (invalid ID or file deleted)
        500: OpenSlide error (corrupted file, unsupported format, missing companions)

    Technical Notes:
        - Opens slide temporarily with OpenSlide
        - Extracts metadata then closes immediately
        - No caching in Phase 1 (will be added in Phase 2)
        - Companion files must be in correct structure (.mrxs requires companion directory)

    Performance:
        - Typical response time: < 100ms
        - Metadata extraction is fast (no image data loaded)

    Examples:
        ```
        GET /api/slides/abc123.../info

        Response:
        {
            "dimensions": [100000, 80000],
            "level_count": 9,
            "vendor": "3DHISTECH"
        }
        ```
    """
    # Implementation
    pass
```

## Verification Checklist

Before considering an endpoint "documented":

- [ ] Docstring complete with all sections
- [ ] Tag appropriately assigned
- [ ] Parameters documented with `Query()` or `Path()`
- [ ] Response structure clearly defined (JSON example)
- [ ] All HTTP error codes documented
- [ ] Technical Notes included if needed
- [ ] Security considerations noted (if applicable)
- [ ] Tested with real data
- [ ] Visible in Swagger UI at `/docs`

## Updating main.py

### When Adding New Tag

```python
# In main.py
app = FastAPI(
    title="VarunaPoC API",
    description="...",
    version="1.0.0",
    openapi_tags=[
        {
            "name": "health",
            "description": "Service health checks"
        },
        {
            "name": "navigation",
            "description": "Slide browsing and navigation"
        },
        {
            "name": "visualization",
            "description": "Slide viewing and rendering"
        },
        {
            "name": "new_category",  # ← ADD HERE
            "description": "Description of new category"
        }
    ]
)
```

### When Adding New Endpoint

Update root endpoint to list new endpoint:

```python
@app.get("/")
async def root():
    return {
        "service": "VarunaPoC API",
        "version": "1.0.0",
        "endpoints": {
            "health": "/api/health",
            "browse_slides": "/api/slides/browse",
            "slide_info": "/api/slides/{id}/info",
            "new_endpoint": "/api/new/endpoint"  # ← ADD HERE
        },
        "documentation": "/docs",
        "alternative_docs": "/redoc"
    }
```

## API Versioning

Increment version in `main.py` based on changes:

- **Major (1.0 → 2.0):** Breaking changes (incompatible with old clients)
- **Minor (1.0 → 1.1):** New endpoints or features (backward compatible)
- **Patch (1.0.0 → 1.0.1):** Bug fixes, documentation improvements

## Testing Documentation

```bash
# Start server
cd backend
uvicorn main:app --reload

# Access Swagger UI
open http://localhost:8000/docs

# Access ReDoc (alternative documentation)
open http://localhost:8000/redoc

# Test endpoint directly
curl http://localhost:8000/api/slides/browse?path=/
```

## Integration with Other Skills

This skill works well with:
- **error-documenter** - Document API error responses
- **manual-updater** - Create user-facing docs after API is complete
- **slide-tester** - Test endpoints with real slide files

## References

- **API Documentation Protocol:** See `CLAUDE.md` section "API Documentation Protocol"
- **FastAPI Documentation:** https://fastapi.tiangolo.com/
- **OpenAPI Specification:** https://swagger.io/specification/
- **Swagger UI:** http://localhost:8000/docs
- **ReDoc:** http://localhost:8000/redoc

## Official Resources

- **FastAPI Best Practices:** https://fastapi.tiangolo.com/tutorial/
- **Pydantic Models:** https://docs.pydantic.dev/latest/
- **OpenAPI Tags:** https://fastapi.tiangolo.com/tutorial/metadata/

---

**Remember:** API documentation is the contract between backend and frontend. Every endpoint must be self-explanatory from its documentation alone.
