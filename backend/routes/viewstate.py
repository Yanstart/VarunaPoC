from fastapi import APIRouter, Depends
from pydantic import BaseModel

from auth.dependencies import get_current_user
from auth.schemas import CurrentUser

router = APIRouter(prefix="/viewstate", tags=["viewstate"])


class ViewStateResponse(BaseModel):
    x: int = 0
    y: int = 0
    z: int = 0
    c: int = 0
    t: int = 0
    level: int = 0
    zoom: float = 1.0
    z_max: int = 1
    c_max: int = 1
    t_max: int = 1
    level_max: int = 1


@router.get("/{slide_id}", response_model=ViewStateResponse)
async def get_viewstate(slide_id: str, _current_user: CurrentUser = Depends(get_current_user)):
    """Get default N-dimensional view state for a slide."""
    # In future: read from slide metadata (OME-TIFF channels/Z/T)
    # For now: return default single-plane state
    from services.nd_viewstate import NDViewState

    state = NDViewState()
    return state.to_dict()
