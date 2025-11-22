"""
Audit Trail Logger
Comprehensive logging for POJK compliance and security auditing
"""
from typing import Dict, Optional, Any
from datetime import datetime
from sqlalchemy.orm import Session
import json
import os
from libs.database.models import AuditTrail, AuditAction


class AuditLogger:
    """
    Centralized audit logging for compliance
    
    Logs all critical actions:
    - User authentication
    - Application submissions
    - Decision changes
    - Document access
    - System configuration changes
    """
    
    def __init__(self, db: Session):
        self.db = db
    
    def log(
        self,
        action: AuditAction,
        user_id: Optional[str],
        entity_type: str,
        entity_id: Optional[str] = None,
        old_value: Optional[Dict] = None,
        new_value: Optional[Dict] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        details: Optional[str] = None
    ) -> AuditTrail:
        """
        Log an audit event
        
        Args:
            action: Type of action (LOGIN, CREATE, UPDATE, DELETE, etc.)
            user_id: ID of user performing action
            entity_type: Type of entity (APPLICATION, DOCUMENT, USER, etc.)
            entity_id: ID of affected entity
            old_value: Previous state (for updates)
            new_value: New state
            ip_address: Client IP address
            user_agent: Client user agent
            details: Additional context
        
        Returns:
            Created AuditTrail record
        """
        audit_entry = AuditTrail(
            action=action,
            user_id=user_id,
            entity_type=entity_type,
            entity_id=entity_id,
            old_value=old_value,
            new_value=new_value,
            ip_address=ip_address,
            user_agent=user_agent,
            details=details,
            timestamp=datetime.utcnow()
        )
        
        self.db.add(audit_entry)
        self.db.commit()
        
        # Also log to file for redundancy
        self._log_to_file(audit_entry)
        
        return audit_entry
    
    def log_authentication(
        self,
        user_id: str,
        email: str,
        success: bool,
        ip_address: str,
        user_agent: str,
        failure_reason: Optional[str] = None
    ):
        """Log authentication attempt"""
        action = AuditAction.LOGIN if success else AuditAction.LOGIN_FAILED
        
        details = f"Authentication {'successful' if success else 'failed'} for {email}"
        if failure_reason:
            details += f": {failure_reason}"
        
        return self.log(
            action=action,
            user_id=user_id if success else None,
            entity_type="USER",
            entity_id=user_id,
            ip_address=ip_address,
            user_agent=user_agent,
            details=details
        )
    
    def log_application_create(
        self,
        user_id: str,
        application_id: str,
        application_data: Dict,
        ip_address: str
    ):
        """Log new application creation"""
        return self.log(
            action=AuditAction.CREATE,
            user_id=user_id,
            entity_type="APPLICATION",
            entity_id=application_id,
            new_value=application_data,
            ip_address=ip_address,
            details=f"New loan application created: {application_id}"
        )
    
    def log_decision_change(
        self,
        user_id: str,
        application_id: str,
        old_decision: str,
        new_decision: str,
        reason: str,
        ip_address: str
    ):
        """Log decision override/change"""
        return self.log(
            action=AuditAction.DECISION_OVERRIDE,
            user_id=user_id,
            entity_type="APPLICATION",
            entity_id=application_id,
            old_value={"decision": old_decision},
            new_value={"decision": new_decision},
            ip_address=ip_address,
            details=f"Decision changed from {old_decision} to {new_decision}: {reason}"
        )
    
    def log_document_access(
        self,
        user_id: str,
        document_id: str,
        action: str,  # VIEW, DOWNLOAD, DELETE
        ip_address: str
    ):
        """Log document access for PII protection compliance"""
        audit_action = {
            'VIEW': AuditAction.VIEW,
            'DOWNLOAD': AuditAction.DOWNLOAD,
            'DELETE': AuditAction.DELETE
        }.get(action, AuditAction.VIEW)
        
        return self.log(
            action=audit_action,
            user_id=user_id,
            entity_type="DOCUMENT",
            entity_id=document_id,
            ip_address=ip_address,
            details=f"Document {action.lower()}: {document_id}"
        )
    
    def log_config_change(
        self,
        user_id: str,
        config_key: str,
        old_value: Any,
        new_value: Any,
        ip_address: str
    ):
        """Log system configuration changes"""
        return self.log(
            action=AuditAction.CONFIG_CHANGE,
            user_id=user_id,
            entity_type="SYSTEM_CONFIG",
            entity_id=config_key,
            old_value={"value": old_value},
            new_value={"value": new_value},
            ip_address=ip_address,
            details=f"Configuration {config_key} changed"
        )
    
    def _log_to_file(self, audit_entry: AuditTrail):
        """Write audit log to file for redundancy"""
        log_dir = os.getenv("AUDIT_LOG_DIR", "./logs/audit")
        os.makedirs(log_dir, exist_ok=True)
        
        # Organize by date
        log_file = os.path.join(
            log_dir,
            f"audit_{datetime.utcnow().strftime('%Y%m%d')}.log"
        )
        
        log_entry = {
            "timestamp": audit_entry.timestamp.isoformat(),
            "action": audit_entry.action.value,
            "user_id": audit_entry.user_id,
            "entity_type": audit_entry.entity_type,
            "entity_id": audit_entry.entity_id,
            "ip_address": audit_entry.ip_address,
            "details": audit_entry.details
        }
        
        with open(log_file, 'a', encoding='utf-8') as f:
            f.write(json.dumps(log_entry) + '\n')
    
    def get_audit_trail(
        self,
        entity_type: Optional[str] = None,
        entity_id: Optional[str] = None,
        user_id: Optional[str] = None,
        action: Optional[AuditAction] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        limit: int = 100
    ) -> list:
        """
        Query audit trail
        
        Returns list of audit entries matching criteria
        """
        query = self.db.query(AuditTrail)
        
        if entity_type:
            query = query.filter(AuditTrail.entity_type == entity_type)
        
        if entity_id:
            query = query.filter(AuditTrail.entity_id == entity_id)
        
        if user_id:
            query = query.filter(AuditTrail.user_id == user_id)
        
        if action:
            query = query.filter(AuditTrail.action == action)
        
        if start_date:
            query = query.filter(AuditTrail.timestamp >= start_date)
        
        if end_date:
            query = query.filter(AuditTrail.timestamp <= end_date)
        
        query = query.order_by(AuditTrail.timestamp.desc()).limit(limit)
        
        return query.all()


# FastAPI Dependency for automatic audit logging
from fastapi import Request

async def get_audit_logger(
    request: Request,
    db: Session
) -> AuditLogger:
    """Dependency injection for audit logger"""
    logger = AuditLogger(db)
    
    # Attach request metadata for automatic logging
    logger.request_ip = request.client.host if request.client else None
    logger.request_user_agent = request.headers.get('User-Agent')
    
    return logger
