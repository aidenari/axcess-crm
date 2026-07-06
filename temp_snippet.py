):
    q = db.query(Lot)
    if batiment_id:
        q = q.where(Lot.batiment_id == batiment_id)
    elif programme_id:
        bat_ids = [b.id for b in db.query(Batiment).filter(Batiment.programme_id == programme_id).all()]
        if bat_ids:
            q = q.where(Lot.batiment_id.in_(bat_ids))
        else:
            return []
    return q.order_by(Lot.id.desc()).all()


@app.post("/lots", response_model=LotRead, status_code=201)
def create_lot(payload: LotCreate, db: Session = Depends(get_db)):
    b = db.get(Batiment, payload.batiment_id)
    if not b:
        raise HTTPException(status_code=404, detail="Bâtiment not found")
    l = Lot(**payload.model_dump(exclude_none=True))
    db.add(l)
    db.commit()
    db.refresh(l)
    return l


@app.put("/lots/{lot_id}", response_model=LotRead)
def update_lot(lot_id: int, patch: LotUpdate, db: Session = Depends(get_db)):
    l = db.get(Lot, lot_id)
    if not l:
        raise HTTPException(status_code=404, detail="Lot not found")
    for k, v in patch.model_dump(exclude_none=True).items():
        setattr(l, k, v)
    db.add(l)
    db.commit()
    db.refresh(l)
    return l


@app.delete("/lots/{lot_id}", status_code=204)
def delete_lot(lot_id: int, db: Session = Depends(get_db)):
    l = db.get(Lot, lot_id)
