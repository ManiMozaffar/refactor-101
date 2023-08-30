# models.py


from typing import Annotated, NewType

import annotated_types
from fastapi import File, Form, UploadFile
from pydantic import PositiveInt

ApiString = Annotated[str, annotated_types.MaxLen(256)]


class UploadedFiles(Base):
    __tablename__ = "uploaded_files"

    id = Column(Integer, autoincrement=True, primary_key=True)
    file = Column(String)
    source = Column(String(255))
    category_id = Column(Integer)
    comment = Column(String)
    user_id = Column(Integer)

    user = relationship(
        "Users",
        foreign_keys=[user_id],
        primaryjoin=lambda: and_(Users.id == Uploaded_files.user_id),
    )

    category_source = relationship(
        "Categories",
        foreign_keys=[categories_id],
        primaryjoin=lambda: and_(Categories.id == Uploaded_files.categories_id),
    )


# serivces.py
from enum import StrEnum, auto


class FileUploadError(Exception):
    ...


class Source(StrEnum):
    CATEGORY = auto()


SafeFile = NewType("SafeFile", UploadFile)


def write_file_to_disk(new_file: SafeFile) -> None:
    with open(f"Uploaded_files/{new_file.filename}", "wb+") as file_object:
        # TODO: use template to save the file, not f string!
        file_object.write(new_file.file.read())
    return None


def create_file_db_obj(
    thisuser,
    comment: ApiString,
    filename: str,
    source: Source,
    category_id: PositiveInt,
) -> UploadedFiles:
    return UploadedFiles(
        file=filename,
        source=source,
        category_id=category_id,
        comment=comment,
        user_id=thisuser.id,
    )


class AcceptedContentType(StrEnum):
    JPG = "..."
    PNG = "..."


def parse_file(new_file: UploadFile, db) -> SafeFile:
    if not new_file.filename:
        raise FileUploadError("No filename detected")

    if new_file.content_type not in AcceptedContentType:
        # TODO: use magic byte to detect file, not `new_file.content_type`
        raise FileUploadError(f"Content type {new_file.content_type} not accepted")

    if not (
        db.query(Categories).filter(Categories.id == category_id).first()
        and source._in(Source)
    ):
        raise FileUploadError

    return SafeFile(new_file)


def create_file(
    new_file: UploadFile,
    source: Source,
    category_id: PositiveInt,
    comment: ApiString,
    thisuser,
    db,
) -> UploadedFiles:
    file = parse_file(new_file, db)
    write_file_to_disk(file)
    assert file.filename is not None
    file_obj = create_file_db_obj(
        source=source,
        comment=comment,
        filename=file.filename,
        thisuser=thisuser,
        category_id=category_id,
    )
    return file_obj


def create_files(
    new_files: list[UploadFile],
    source: Source,
    category_id: PositiveInt,
    comment: ApiString,
    thisuser,
    db,
) -> tuple[list[UploadedFiles], list[FileUploadError]]:
    errors: list[FileUploadError] = []
    uploaded_files: list[UploadedFiles] = []
    for new_file in new_files:
        try:
            file = create_file(
                new_file=new_file,
                source=source,
                comment=comment,
                thisuser=thisuser,
                category_id=category_id,
                db=db,
            )
            uploaded_files.append(file)
        except FileUploadError as error:
            errors.append(error)

    return (uploaded_files, errors)


# router.py


@uploaded_files_router.post("/create")
def files_create(
    new_files: list[UploadFile],
    source: Source = Form(...),
    category_id: int = Form(...),
    comment: ApiString = Form(None),
    db: Session = Depends(database),
    current_user: CreateUser = Depends(get_current_active_user),
):
    role_verification(current_user)
    files = create_files(new_files, source, category_id, comment, current_user, db)
    with db.begin_session():
        db.add_all(files)
        db.commit()
