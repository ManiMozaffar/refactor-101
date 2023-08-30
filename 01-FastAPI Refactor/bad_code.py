# models.py


class Uploaded_files(Base):
    tablename = "uploaded_files"
    id = Column(Integer, autoincrement=True, primary_key=True)
    file = Column(String)
    source = Column(String(255))
    source_id = Column(Integer)
    comment = Column(String(255))
    user_id = Column(Integer)

    user = relationship(
        "Users",
        foreign_keys=[user_id],
        primaryjoin=lambda: and_(Users.id == Uploaded_files.user_id),
    )

    category_source = relationship(
        "Categories",
        foreign_keys=[source_id],
        primaryjoin=lambda: and_(Categories.id == Uploaded_files.source_id),
    )


# serivces.py


def create_file(new_files, source, source_id, comment, thisuser, db):
    for new_file in new_files:
        if source not in ["category"]:
            raise HTTPException(status_code=400, detail="Source error")
        # if db.query(Uploaded_files).filter(Uploaded_files.source == source,
        #                                    Uploaded_files.source_id == source_id).first():
        #     raise HTTPException(status_code=400, detail="This source already have his own file!")
        if (
            db.query(Categories).filter(Categories.id == source_id).first()
            and source == "category"
        ):
            file_location = new_file.filename
            assert file_location is not None
            ext = os.path.splitext(file_location)[-1].lower()
            if ext not in [".jpg", ".png", ".mp3", ".mp4", ".gif", ".jpeg"]:
                raise HTTPException(
                    status_code=400, detail="Yuklanayotgan fayl formati mos kelmaydi!"
                )
            with open(f"Uploaded_files/{new_file.filename}", "wb+") as file_object:
                file_object.write(new_file.file.read())
            new_file_db = Uploaded_files(
                file=new_file.filename,
                source=source,
                source_id=source_id,
                comment=comment,
                user_id=thisuser.id,
            )
            save_in_db(db, new_file_db)

        else:
            raise HTTPException(
                status_code=400, detail="source va source_id bir-biriga mos kelmadi!"
            )


# router.py


@uploaded_files_router.post("/create")
def file_create(
    new_files: list[UploadFile],
    source: str = Form(...),
    source_id: int = Form(...),
    comment: str = Form(None),
    db: Session = Depends(database),
    current_user: CreateUser = Depends(get_current_active_user),
):
    assert get_size(new_files) > 10_000_000
    role_verification(current_user, inspect.currentframe().f_code.co_name)

    create_file(new_files, source, source_id, comment, current_user, db)
