import logging

from fastapi import APIRouter, Header, HTTPException, Query

from ..models.favorite import FavoriteRequest, FavoriteResponse
from ..repositories.favorite_repository import (
    add_favorite,
    get_favorites,
    delete_favorite,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/favorites", tags=["favorites"])


@router.post("", status_code=201)
def save_favorite(
    request: FavoriteRequest,
    x_auth_code: str = Header(default="", alias="X-Auth-Code"),
):
    """收藏一个院校。"""
    if not x_auth_code:
        raise HTTPException(status_code=401, detail="缺少 X-Auth-Code 请求头")
    try:
        data = request.model_dump(exclude_none=True)
        result = add_favorite(auth_code=x_auth_code, school_data=data)
        return FavoriteResponse(**result)
    except ValueError as e:
        raise HTTPException(status_code=409, detail=str(e))
    except Exception as e:
        logger.error("save favorite error: %s", str(e), exc_info=True)
        raise HTTPException(status_code=500, detail="收藏院校失败")


@router.get("")
def list_favorites(
    x_auth_code: str = Header(default="", alias="X-Auth-Code"),
):
    """获取用户所有收藏院校。"""
    if not x_auth_code:
        raise HTTPException(status_code=401, detail="缺少 X-Auth-Code 请求头")
    try:
        rows = get_favorites(auth_code=x_auth_code)
        return {"favorites": [FavoriteResponse(**r) for r in rows]}
    except Exception as e:
        logger.error("list favorites error: %s", str(e), exc_info=True)
        raise HTTPException(status_code=500, detail="获取收藏列表失败")


@router.delete("")
def remove_favorite(
    x_auth_code: str = Header(default="", alias="X-Auth-Code"),
    school_name: str = Query(default="", min_length=1),
):
    """删除一个收藏院校。"""
    if not x_auth_code:
        raise HTTPException(status_code=401, detail="缺少 X-Auth-Code 请求头")
    if not school_name:
        raise HTTPException(status_code=400, detail="缺少 school_name 查询参数")
    try:
        deleted = delete_favorite(auth_code=x_auth_code, school_name=school_name)
        if not deleted:
            raise HTTPException(status_code=404, detail=f"未找到院校 '{school_name}'")
        return {"ok": True, "school_name": school_name}
    except HTTPException:
        raise
    except Exception as e:
        logger.error("delete favorite error: %s", str(e), exc_info=True)
        raise HTTPException(status_code=500, detail="删除收藏院校失败")
