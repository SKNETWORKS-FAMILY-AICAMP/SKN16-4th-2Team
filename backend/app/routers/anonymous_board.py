"""
익명 게시판 (대나무숲) API 라우터
완전 익명성 보장
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select
from typing import List

from app.database import get_session
from app.models.user import User
from app.models.post import (
    Post, PostCreate, PostRead, PostDetail,
    Comment, CommentCreate, CommentRead,
    PostLike, CommentLike
)
from app.utils.auth import get_current_user

router = APIRouter(prefix="/posts", tags=["Anonymous Board"])


@router.post("/", response_model=PostRead)
async def create_post(
    post_data: PostCreate,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    """
    게시글 작성
    - 작성자는 "글쓴이"로 표시
    """
    post = Post(
        title=post_data.title,
        content=post_data.content,
        author_id=current_user.id
    )
    
    session.add(post)
    session.commit()
    session.refresh(post)
    
    return PostRead(
        id=post.id,
        title=post.title,
        content=post.content,
        view_count=post.view_count,
        comment_count=post.comment_count,
        created_at=post.created_at,
        updated_at=post.updated_at,
        author_alias="글쓴이"
    )


@router.get("/", response_model=List[PostRead])
async def get_posts(
    skip: int = 0,
    limit: int = 20,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    """
    게시글 목록 조회
    - 삭제되지 않은 게시글만
    - 최신순 정렬
    - 목록에서는 작성자 정보 숨김
    - 추천/비추천 정보 포함
    """
    statement = (
        select(Post)
        .where(Post.is_deleted == False)
        .order_by(Post.created_at.desc())
        .offset(skip)
        .limit(limit)
    )
    
    posts = session.exec(statement).all()
    
    result = []
    
    for post in posts:
        # 추천/비추천 수 계산
        like_count = session.exec(
            select(PostLike).where(PostLike.post_id == post.id, PostLike.is_like == True)
        ).all()
        dislike_count = session.exec(
            select(PostLike).where(PostLike.post_id == post.id, PostLike.is_like == False)
        ).all()
        
        # 현재 사용자의 추천/비추천 상태 확인
        user_like = session.exec(
            select(PostLike).where(
                PostLike.post_id == post.id, 
                PostLike.user_id == current_user.id,
                PostLike.is_like == True
            )
        ).first()
        user_dislike = session.exec(
            select(PostLike).where(
                PostLike.post_id == post.id, 
                PostLike.user_id == current_user.id,
                PostLike.is_like == False
            )
        ).first()
        
        result.append(PostRead(
            id=post.id,
            title=post.title,
            content=post.content,
            view_count=post.view_count,
            comment_count=post.comment_count,
            like_count=len(like_count),
            dislike_count=len(dislike_count),
            user_liked=user_like is not None,
            user_disliked=user_dislike is not None,
            created_at=post.created_at,
            updated_at=post.updated_at,
            author_alias="익명1"  # 목록에서는 익명1로 표시
        ))
    
    return result


@router.get("/{post_id}", response_model=PostDetail)
async def get_post(
    post_id: int,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    """
    게시글 상세 조회
    - 조회수 증가
    - 댓글 목록 포함
    - 게시글 작성자는 모든 사용자에게 "글쓴이"로 표시
    - 댓글 작성자는 게시글 작성자인 경우 "글쓴이", 다른 사람은 "익명1", "익명2" 순으로 표시
    """
    statement = select(Post).where(Post.id == post_id, Post.is_deleted == False)
    post = session.exec(statement).first()
    
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")
    
    # 조회수 증가
    post.view_count += 1
    session.add(post)
    session.commit()
    
    # 댓글 조회
    comment_statement = (
        select(Comment)
        .where(Comment.post_id == post_id, Comment.is_deleted == False)
        .order_by(Comment.created_at.asc())
    )
    comments = session.exec(comment_statement).all()
    
    # 게시글 작성자 표시 (모든 사용자에게 "글쓴이"로 표시)
    post_author_alias = "글쓴이"
    
    # 게시글 추천/비추천 수 계산
    post_like_count = session.exec(
        select(PostLike).where(PostLike.post_id == post_id, PostLike.is_like == True)
    ).all()
    post_dislike_count = session.exec(
        select(PostLike).where(PostLike.post_id == post_id, PostLike.is_like == False)
    ).all()
    
    # 현재 사용자의 게시글 추천/비추천 상태 확인
    user_post_like = session.exec(
        select(PostLike).where(
            PostLike.post_id == post_id, 
            PostLike.user_id == current_user.id,
            PostLike.is_like == True
        )
    ).first()
    user_post_dislike = session.exec(
        select(PostLike).where(
            PostLike.post_id == post_id, 
            PostLike.user_id == current_user.id,
            PostLike.is_like == False
        )
    ).first()
    
    # 댓글에 익명 번호 부여 및 추천/비추천 정보 포함
    comment_reads = []
    anonymous_counter = 1
    
    for comment in comments:
        if comment.author_id == post.author_id:
            # 게시글 작성자가 댓글을 쓴 경우 "글쓴이"로 표시
            author_alias = "글쓴이"
        else:
            # 다른 사람이 댓글을 쓴 경우 익명1, 익명2... 순으로 표시
            author_alias = f"익명{anonymous_counter}"
            anonymous_counter += 1
        
        # 댓글 추천/비추천 수 계산
        comment_like_count = session.exec(
            select(CommentLike).where(CommentLike.comment_id == comment.id, CommentLike.is_like == True)
        ).all()
        comment_dislike_count = session.exec(
            select(CommentLike).where(CommentLike.comment_id == comment.id, CommentLike.is_like == False)
        ).all()
        
        # 현재 사용자의 댓글 추천/비추천 상태 확인
        user_comment_like = session.exec(
            select(CommentLike).where(
                CommentLike.comment_id == comment.id, 
                CommentLike.user_id == current_user.id,
                CommentLike.is_like == True
            )
        ).first()
        user_comment_dislike = session.exec(
            select(CommentLike).where(
                CommentLike.comment_id == comment.id, 
                CommentLike.user_id == current_user.id,
                CommentLike.is_like == False
            )
        ).first()
        
        comment_reads.append(CommentRead(
            id=comment.id,
            post_id=comment.post_id,
            content=comment.content,
            like_count=len(comment_like_count),
            dislike_count=len(comment_dislike_count),
            user_liked=user_comment_like is not None,
            user_disliked=user_comment_dislike is not None,
            created_at=comment.created_at,
            author_alias=author_alias,
            is_author=comment.author_id == current_user.id,
            is_admin=current_user.role.value == "admin"
        ))
    
    return PostDetail(
        post=PostRead(
            id=post.id,
            title=post.title,
            content=post.content,
            view_count=post.view_count,
            comment_count=post.comment_count,
            like_count=len(post_like_count),
            dislike_count=len(post_dislike_count),
            user_liked=user_post_like is not None,
            user_disliked=user_post_dislike is not None,
            created_at=post.created_at,
            updated_at=post.updated_at,
            author_alias=post_author_alias
        ),
        comments=comment_reads,
        is_author=post.author_id == current_user.id,
        is_admin=current_user.role.value == "admin"
    )


@router.post("/comments", response_model=CommentRead)
async def create_comment(
    comment_data: CommentCreate,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    """
    댓글 작성
    - 작성자는 "글쓴이"로 표시
    - 게시글 댓글 수 증가
    """
    # 게시글 존재 확인
    post_statement = select(Post).where(Post.id == comment_data.post_id)
    post = session.exec(post_statement).first()
    
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")
    
    # 댓글 순서 계산
    comment_count_statement = select(Comment).where(
        Comment.post_id == comment_data.post_id,
        Comment.is_deleted == False
    )
    existing_comments = session.exec(comment_count_statement).all()
    comment_order = len(existing_comments) + 1  # 순서는 1부터 시작
    
    # 댓글 생성
    comment = Comment(
        post_id=comment_data.post_id,
        content=comment_data.content,
        author_id=current_user.id,
        comment_order=comment_order
    )
    
    session.add(comment)
    
    # 게시글 댓글 수 증가
    post.comment_count += 1
    session.add(post)
    
    session.commit()
    session.refresh(comment)
    
    # 게시글 작성자 확인
    post_statement = select(Post).where(Post.id == comment_data.post_id)
    post = session.exec(post_statement).first()
    
    if comment.author_id == post.author_id:
        # 게시글 작성자가 댓글을 쓴 경우 "글쓴이"로 표시
        author_alias = "글쓴이"
    else:
        # 다른 사람이 댓글을 쓴 경우 익명 번호 할당
        existing_comments_count = len(existing_comments)
        comment_anonymous_number = existing_comments_count + 1
        author_alias = f"익명{comment_anonymous_number}"
    
    return CommentRead(
        id=comment.id,
        post_id=comment.post_id,
        content=comment.content,
        created_at=comment.created_at,
        author_alias=author_alias,
        is_author=True,  # 댓글 작성자는 본인이므로 항상 True
        is_admin=current_user.role.value == "admin"
    )


@router.delete("/{post_id}")
async def delete_post(
    post_id: int,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    """
    게시글 삭제
    - 작성자 본인 또는 관리자만 삭제 가능
    - 소프트 삭제 (is_deleted = True)
    """
    statement = select(Post).where(Post.id == post_id)
    post = session.exec(statement).first()
    
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")
    
    # 작성자 또는 관리자 확인
    if post.author_id != current_user.id and current_user.role.value != "admin":
        raise HTTPException(status_code=403, detail="Not authorized to delete this post")
    
    post.is_deleted = True
    session.add(post)
    session.commit()
    
    return {"message": "Post deleted successfully"}


@router.delete("/comments/{comment_id}")
async def delete_comment(
    comment_id: int,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    """
    댓글 삭제
    - 작성자 본인 또는 관리자만 삭제 가능
    """
    statement = select(Comment).where(Comment.id == comment_id)
    comment = session.exec(statement).first()
    
    if not comment:
        raise HTTPException(status_code=404, detail="Comment not found")
    
    # 작성자 또는 관리자 확인
    if comment.author_id != current_user.id and current_user.role.value != "admin":
        raise HTTPException(status_code=403, detail="Not authorized to delete this comment")
    
    comment.is_deleted = True
    session.add(comment)
    
    # 게시글 댓글 수 감소
    post_statement = select(Post).where(Post.id == comment.post_id)
    post = session.exec(post_statement).first()
    if post:
        post.comment_count = max(0, post.comment_count - 1)
        session.add(post)
    
    session.commit()
    
    return {"message": "Comment deleted successfully"}


# 게시글 추천/비추천 API
@router.post("/{post_id}/like")
async def like_post(
    post_id: int,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    """게시글 추천"""
    # 게시글 존재 확인
    post = session.exec(select(Post).where(Post.id == post_id, Post.is_deleted == False)).first()
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")
    
    # 기존 추천/비추천 확인
    existing_like = session.exec(
        select(PostLike).where(
            PostLike.post_id == post_id,
            PostLike.user_id == current_user.id
        )
    ).first()
    
    if existing_like:
        if existing_like.is_like:
            # 이미 추천한 경우 취소
            session.delete(existing_like)
        else:
            # 비추천을 추천으로 변경
            existing_like.is_like = True
            session.add(existing_like)
    else:
        # 새로운 추천 추가
        new_like = PostLike(
            post_id=post_id,
            user_id=current_user.id,
            is_like=True
        )
        session.add(new_like)
    
    session.commit()
    return {"message": "Post liked successfully"}


@router.delete("/{post_id}/like")
async def unlike_post(
    post_id: int,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    """게시글 추천 취소"""
    existing_like = session.exec(
        select(PostLike).where(
            PostLike.post_id == post_id,
            PostLike.user_id == current_user.id,
            PostLike.is_like == True
        )
    ).first()
    
    if existing_like:
        session.delete(existing_like)
        session.commit()
    
    return {"message": "Post unliked successfully"}


@router.post("/{post_id}/dislike")
async def dislike_post(
    post_id: int,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    """게시글 비추천"""
    # 게시글 존재 확인
    post = session.exec(select(Post).where(Post.id == post_id, Post.is_deleted == False)).first()
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")
    
    # 기존 추천/비추천 확인
    existing_like = session.exec(
        select(PostLike).where(
            PostLike.post_id == post_id,
            PostLike.user_id == current_user.id
        )
    ).first()
    
    if existing_like:
        if not existing_like.is_like:
            # 이미 비추천한 경우 취소
            session.delete(existing_like)
        else:
            # 추천을 비추천으로 변경
            existing_like.is_like = False
            session.add(existing_like)
    else:
        # 새로운 비추천 추가
        new_like = PostLike(
            post_id=post_id,
            user_id=current_user.id,
            is_like=False
        )
        session.add(new_like)
    
    session.commit()
    return {"message": "Post disliked successfully"}


@router.delete("/{post_id}/dislike")
async def undislike_post(
    post_id: int,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    """게시글 비추천 취소"""
    existing_like = session.exec(
        select(PostLike).where(
            PostLike.post_id == post_id,
            PostLike.user_id == current_user.id,
            PostLike.is_like == False
        )
    ).first()
    
    if existing_like:
        session.delete(existing_like)
        session.commit()
    
    return {"message": "Post undisliked successfully"}


# 댓글 추천/비추천 API
@router.post("/comments/{comment_id}/like")
async def like_comment(
    comment_id: int,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    """댓글 추천"""
    # 댓글 존재 확인
    comment = session.exec(select(Comment).where(Comment.id == comment_id, Comment.is_deleted == False)).first()
    if not comment:
        raise HTTPException(status_code=404, detail="Comment not found")
    
    # 기존 추천/비추천 확인
    existing_like = session.exec(
        select(CommentLike).where(
            CommentLike.comment_id == comment_id,
            CommentLike.user_id == current_user.id
        )
    ).first()
    
    if existing_like:
        if existing_like.is_like:
            # 이미 추천한 경우 취소
            session.delete(existing_like)
        else:
            # 비추천을 추천으로 변경
            existing_like.is_like = True
            session.add(existing_like)
    else:
        # 새로운 추천 추가
        new_like = CommentLike(
            comment_id=comment_id,
            user_id=current_user.id,
            is_like=True
        )
        session.add(new_like)
    
    session.commit()
    return {"message": "Comment liked successfully"}


@router.delete("/comments/{comment_id}/like")
async def unlike_comment(
    comment_id: int,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    """댓글 추천 취소"""
    existing_like = session.exec(
        select(CommentLike).where(
            CommentLike.comment_id == comment_id,
            CommentLike.user_id == current_user.id,
            CommentLike.is_like == True
        )
    ).first()
    
    if existing_like:
        session.delete(existing_like)
        session.commit()
    
    return {"message": "Comment unliked successfully"}


@router.post("/comments/{comment_id}/dislike")
async def dislike_comment(
    comment_id: int,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    """댓글 비추천"""
    # 댓글 존재 확인
    comment = session.exec(select(Comment).where(Comment.id == comment_id, Comment.is_deleted == False)).first()
    if not comment:
        raise HTTPException(status_code=404, detail="Comment not found")
    
    # 기존 추천/비추천 확인
    existing_like = session.exec(
        select(CommentLike).where(
            CommentLike.comment_id == comment_id,
            CommentLike.user_id == current_user.id
        )
    ).first()
    
    if existing_like:
        if not existing_like.is_like:
            # 이미 비추천한 경우 취소
            session.delete(existing_like)
        else:
            # 추천을 비추천으로 변경
            existing_like.is_like = False
            session.add(existing_like)
    else:
        # 새로운 비추천 추가
        new_like = CommentLike(
            comment_id=comment_id,
            user_id=current_user.id,
            is_like=False
        )
        session.add(new_like)
    
    session.commit()
    return {"message": "Comment disliked successfully"}


@router.delete("/comments/{comment_id}/dislike")
async def undislike_comment(
    comment_id: int,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    """댓글 비추천 취소"""
    existing_like = session.exec(
        select(CommentLike).where(
            CommentLike.comment_id == comment_id,
            CommentLike.user_id == current_user.id,
            CommentLike.is_like == False
        )
    ).first()
    
    if existing_like:
        session.delete(existing_like)
        session.commit()
    
    return {"message": "Comment undisliked successfully"}

