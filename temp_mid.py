        "message": f"{settings.APP_NAME} backend is running",
        "docs": "/docs",
        "redoc": "/redoc",
        "health": "/health",
    }


@app.get("/health")
def health(db: Session = Depends(get_db)):
    # DB ping for a real connectivity check
    db.execute(text("SELECT 1"))
    return {"status": "ok", "app": settings.APP_NAME, "env": settings.APP_ENV}


# --- Users minimal CRUD ---
@app.get("/users", response_model=list[UserRead])
def list_users(db: Session = Depends(get_db)):
    return db.query(User).order_by(User.id.desc()).all()


@app.get("/users/id/{user_id}", response_model=UserRead)
def get_user_by_id(user_id: int, db: Session = Depends(get_db)):
    user = db.get(User, user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    return user


app.include_router(auth_router)


# ----------------- Programmes -----------------

@app.get("/programmes", response_model=list[ProgrammeRead])
def list_programmes(db: Session = Depends(get_db)):
    return db.query(Programme).order_by(Programme.id.desc()).all()


@app.post("/programmes", response_model=ProgrammeRead, status_code=201)
def create_programme(payload: ProgrammeCreate, db: Session = Depends(get_db)):
    p = Programme(**payload.model_dump(exclude_none=True))
    db.add(p)
    db.commit()
    db.refresh(p)
    return p


@app.get("/programmes/{programme_id}", response_model=ProgrammeRead)
def get_programme(programme_id: int, db: Session = Depends(get_db)):
    p = db.get(Programme, programme_id)
    if not p:
        raise HTTPException(status_code=404, detail="Programme not found")
    return p


@app.get("/programmes/{programme_id}/statistics", response_model=LotsStatistics)
def programme_statistics(programme_id: int, db: Session = Depends(get_db)):
    # gather lots for programme via batiments
    bat_ids = [b.id for b in db.query(Batiment).filter(Batiment.programme_id == programme_id).all()]
    lots = []
    if bat_ids:
        lots = db.query(Lot).filter(Lot.batiment_id.in_(bat_ids)).all()
    return _compute_stats(lots)


# ----------------- Bâtiments -----------------

@app.get("/batiments", response_model=list[BatimentRead])
def list_batiments(programme_id: int = Query(...), db: Session = Depends(get_db)):
    return db.query(Batiment).where(Batiment.programme_id == programme_id).order_by(Batiment.id.desc()).all()


@app.post("/batiments", response_model=BatimentRead, status_code=201)
def create_batiment(payload: BatimentCreate, db: Session = Depends(get_db)):
    if not db.get(Programme, payload.programme_id):
        raise HTTPException(status_code=404, detail="Programme not found")
    b = Batiment(**payload.model_dump(exclude_none=True))
    db.add(b)
    db.commit()
    db.refresh(b)
    return b
