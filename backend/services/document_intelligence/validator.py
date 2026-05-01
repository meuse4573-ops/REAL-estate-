"""
Texas TREC Document Validator.
Validates extracted contract data against TREC requirements.
"""
from typing import Dict, Any, List
from datetime import datetime, date


class TRECValidator:
    """Validates extracted TREC contract data."""
    
    REQUIRED_FIELDS = [
        "property_address",
        "purchase_price",
        "buyers",
        "sellers",
    ]
    
    DEADLINE_TYPES = [
        "inspection",
        "financing_contingency", 
        "appraisal",
        "title_commitment",
        "closing",
        "possession",
        "option_period"
    ]
    
    def validate(self, extraction: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate extracted TREC contract data.
        
        Args:
            extraction: Extracted data dictionary
            
        Returns:
            Validation result with is_valid, errors, warnings
        """
        errors = []
        warnings = []
        
        errors.extend(self._validate_required_fields(extraction))
        warnings.extend(self._validate_optional_fields(extraction))
        
        deadlines_valid, deadline_errors = self._validate_deadlines(extraction.get("deadlines", []))
        errors.extend(deadline_errors)
        
        dates_valid, date_warnings = self._validate_dates(extraction)
        warnings.extend(date_warnings)
        
        return {
            "is_valid": len(errors) == 0,
            "errors": errors,
            "warnings": warnings,
            "deadlines_valid": deadlines_valid,
            "score": self._calculate_validity_score(extraction, errors, warnings)
        }
    
    def _validate_required_fields(self, data: Dict) -> List[str]:
        """Check required fields are present and non-empty."""
        errors = []
        
        for field in self.REQUIRED_FIELDS:
            value = data.get(field)
            
            if value is None:
                errors.append(f"Required field '{field}' is missing")
            elif isinstance(value, (str, list)) and len(value) == 0:
                errors.append(f"Required field '{field}' is empty")
            elif isinstance(value, (int, float)) and value <= 0:
                errors.append(f"Required field '{field}' must be positive")
        
        return errors
    
    def _validate_optional_fields(self, data: Dict) -> List[str]:
        """Check optional fields and warn about missing data."""
        warnings = []
        
        if not data.get("earnest_money"):
            warnings.append("Earnest money amount not found")
        
        if not data.get("option_fee") and data.get("option_period_days"):
            warnings.append("Option period specified but no option fee found")
        
        if not data.get("closing_date"):
            warnings.append("Closing date not specified")
        
        if not data.get("title_company"):
            warnings.append("Title company not identified")
        
        return warnings
    
    def _validate_deadlines(self, deadlines: List[Dict]) -> tuple:
        """Validate deadline entries."""
        errors = []
        
        if not deadlines:
            return True, ["No deadlines extracted from contract"]
        
        for i, deadline in enumerate(deadlines):
            if not deadline.get("type"):
                errors.append(f"Deadline {i+1}: Missing type")
            elif deadline["type"] not in self.DEADLINE_TYPES:
                errors.append(f"Deadline {i+1}: Invalid type '{deadline['type']}'")
            
            if not deadline.get("date"):
                errors.append(f"Deadline {i+1}: Missing date")
        
        return len(errors) == 0, errors
    
    def _validate_dates(self, data: Dict) -> tuple:
        """Validate date values are reasonable."""
        warnings = []
        
        acceptance = data.get("acceptance_date")
        closing = data.get("closing_date")
        
        if acceptance and closing:
            try:
                acc_date = datetime.strptime(acceptance, "%Y-%m-%d").date() if isinstance(acceptance, str) else acceptance
                close_date = datetime.strptime(closing, "%Y-%m-%d").date() if isinstance(closing, str) else closing
                
                if close_date < acc_date:
                    warnings.append("Closing date is before acceptance date")
                
                days_diff = (close_date - acc_date).days
                if days_diff > 365:
                    warnings.append("Contract term exceeds 365 days - verify dates")
            except:
                pass
        
        return True, warnings
    
    def _calculate_validity_score(self, data: Dict, errors: List[str], warnings: List[str]) -> float:
        """Calculate overall validity score (0-100)."""
        base_score = 100
        base_score -= len(errors) * 20
        base_score -= len(warnings) * 5
        return max(0, base_score / 100)


trec_validator = TRECValidator()