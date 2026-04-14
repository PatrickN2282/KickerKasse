from sqlalchemy.orm import Session
from app.models import ZBonHistory
from sqlalchemy import desc


class ZBonHistoryRepository:
    """Repository for ZBonHistory model"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def create(self, **kwargs) -> ZBonHistory:
        """Create new Z-Bon history record"""
        zbon = ZBonHistory(**kwargs)
        self.db.add(zbon)
        self.db.commit()
        self.db.refresh(zbon)
        return zbon
    
    def get_by_id(self, zbon_id: int) -> ZBonHistory:
        """Get Z-Bon by ID"""
        return self.db.query(ZBonHistory).filter(ZBonHistory.id == zbon_id).first()
    
    def get_by_sequence(self, sequence_number: int) -> ZBonHistory:
        """Get Z-Bon by sequence number"""
        return self.db.query(ZBonHistory).filter(
            ZBonHistory.sequence_number == sequence_number
        ).first()
    
    def get_latest(self) -> ZBonHistory:
        """Get latest Z-Bon"""
        return self.db.query(ZBonHistory).order_by(
            desc(ZBonHistory.sequence_number)
        ).first()
    
    def get_all(self) -> list:
        """Get all Z-Bon records, ordered by sequence descending"""
        return self.db.query(ZBonHistory).order_by(
            desc(ZBonHistory.sequence_number)
        ).all()
    
    def update(self, zbon_id: int, **kwargs) -> ZBonHistory:
        """Update Z-Bon record"""
        zbon = self.get_by_id(zbon_id)
        if not zbon:
            return None
        
        for key, value in kwargs.items():
            if hasattr(zbon, key):
                setattr(zbon, key, value)
        
        self.db.commit()
        self.db.refresh(zbon)
        return zbon
    
    def delete(self, zbon_id: int) -> bool:
        """Delete Z-Bon record"""
        zbon = self.get_by_id(zbon_id)
        if not zbon:
            return False
        
        self.db.delete(zbon)
        self.db.commit()
        return True
