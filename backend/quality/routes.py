"""
Quality Routes - API endpoints for inter-annotator agreement metrics.

All computation endpoints use POST (complex parameters, not simple reads).
"""

import logging

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from auth.dependencies import get_current_user
from auth.schemas import CurrentUser
from core.database import get_db
from quality.schemas import (
    AnnotatorInfo,
    ConfusionMatrixResult,
    DisagreementHeatmapResult,
    FleissKappaResult,
    IoUDistributionResult,
    KappaResult,
    MultiRaterRequest,
    PairwiseRequest,
    PerLabelMetricsResult,
)
from quality.services import (
    compute_confusion_matrix,
    compute_disagreement_heatmap,
    compute_fleiss_kappa,
    compute_iou_distribution,
    compute_pairwise_kappa,
    compute_per_label_metrics,
    get_annotators,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/quality", tags=["Quality Metrics"])


@router.get("/{slide_id}/annotators", response_model=list[AnnotatorInfo])
async def list_annotators(
    slide_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user),
):
    """List annotators who have annotated a slide."""
    try:
        return await get_annotators(db, slide_id)
    except Exception as e:
        logger.error(f"Failed to get annotators for {slide_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{slide_id}/kappa", response_model=KappaResult)
async def compute_kappa(
    slide_id: str,
    request: PairwiseRequest,
    db: AsyncSession = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user),
):
    """Compute Cohen's kappa between two annotators."""
    try:
        return await compute_pairwise_kappa(
            db,
            slide_id,
            annotator_a=request.annotator_a,
            annotator_b=request.annotator_b,
            iou_threshold=request.iou_threshold,
            matching_strategy=request.matching_strategy,
            grid_cell_size=request.grid_cell_size,
            point_buffer_radius=request.point_buffer_radius,
        )
    except Exception as e:
        logger.error(f"Failed to compute kappa for {slide_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{slide_id}/fleiss", response_model=FleissKappaResult)
async def compute_fleiss(
    slide_id: str,
    request: MultiRaterRequest,
    db: AsyncSession = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user),
):
    """Compute Fleiss' kappa for multiple annotators."""
    try:
        return await compute_fleiss_kappa(
            db,
            slide_id,
            annotators=request.annotators,
            grid_cell_size=request.grid_cell_size,
            point_buffer_radius=request.point_buffer_radius,
        )
    except Exception as e:
        logger.error(f"Failed to compute Fleiss' kappa for {slide_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{slide_id}/confusion-matrix", response_model=ConfusionMatrixResult)
async def get_confusion_matrix(
    slide_id: str,
    request: PairwiseRequest,
    db: AsyncSession = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user),
):
    """Compute confusion matrix between two annotators."""
    try:
        return await compute_confusion_matrix(
            db,
            slide_id,
            annotator_a=request.annotator_a,
            annotator_b=request.annotator_b,
            iou_threshold=request.iou_threshold,
            matching_strategy=request.matching_strategy,
            grid_cell_size=request.grid_cell_size,
            point_buffer_radius=request.point_buffer_radius,
        )
    except Exception as e:
        logger.error(f"Failed to compute confusion matrix for {slide_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{slide_id}/f1", response_model=PerLabelMetricsResult)
async def get_f1_metrics(
    slide_id: str,
    request: PairwiseRequest,
    db: AsyncSession = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user),
):
    """Compute per-label F1/precision/recall between two annotators."""
    try:
        return await compute_per_label_metrics(
            db,
            slide_id,
            annotator_a=request.annotator_a,
            annotator_b=request.annotator_b,
            iou_threshold=request.iou_threshold,
            matching_strategy=request.matching_strategy,
            grid_cell_size=request.grid_cell_size,
            point_buffer_radius=request.point_buffer_radius,
        )
    except Exception as e:
        logger.error(f"Failed to compute F1 metrics for {slide_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{slide_id}/iou-distribution", response_model=IoUDistributionResult)
async def get_iou_distribution(
    slide_id: str,
    request: PairwiseRequest,
    db: AsyncSession = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user),
):
    """Compute IoU distribution between two annotators."""
    try:
        return await compute_iou_distribution(
            db,
            slide_id,
            annotator_a=request.annotator_a,
            annotator_b=request.annotator_b,
            iou_threshold=0.0,  # Capture all overlaps for distribution
            point_buffer_radius=request.point_buffer_radius,
        )
    except Exception as e:
        logger.error(f"Failed to compute IoU distribution for {slide_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{slide_id}/disagreements", response_model=DisagreementHeatmapResult)
async def get_disagreements(
    slide_id: str,
    request: PairwiseRequest,
    db: AsyncSession = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user),
):
    """Get disagreement regions between two annotators as GeoJSON."""
    try:
        return await compute_disagreement_heatmap(
            db,
            slide_id,
            annotator_a=request.annotator_a,
            annotator_b=request.annotator_b,
            iou_threshold=request.iou_threshold,
            point_buffer_radius=request.point_buffer_radius,
        )
    except Exception as e:
        logger.error(f"Failed to compute disagreements for {slide_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))
