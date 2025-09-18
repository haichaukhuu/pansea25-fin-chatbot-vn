from datetime import datetime
from typing import Dict, Any, Optional, List
from pydantic import BaseModel, Field, validator
import uuid
import json


class QuestionnaireAnswer(BaseModel):
    """
    Model for questionnaire answers from the onboarding process.
    """
    
    # Question 1: Loại hoạt động nông nghiệp (checkboxes)
    agricultural_activity: List[str] = Field(
        alias="agriculturalActivity",
        description="Types of agricultural activities (multiple selection)"
    )
    
    # Question 2: Loại cây trồng (text)
    crop_type: str = Field(
        alias="cropType",
        description="Type of crops grown"
    )
    
    # Question 3: Loại vật nuôi (text) 
    livestock_type: str = Field(
        alias="livestockType",
        description="Type of livestock"
    )
    
    # Question 4: Bạn sống ở khu vực nào? (dropdown)
    location: str = Field(
        description="Location/province where user lives"
    )
    
    # Question 5: Quy mô canh tác (checkboxes - but frontend shows radio buttons)
    farm_scale: str = Field(
        alias="farmScale",
        description="Scale of farming operation"
    )
    
    # Question 6: Bạn muốn được hỗ trợ về mặt gì? (checkboxes)
    support_needs: List[str] = Field(
        alias="supportNeeds",
        description="Areas where user needs support (multiple selection)"
    )
    
    # Question 7: Mức độ hiểu biết về tài chính (checkboxes - but frontend shows radio buttons)
    financial_knowledge: str = Field(
        alias="financialKnowledge",
        description="Level of financial knowledge"
    )
    
    @validator('agricultural_activity', 'support_needs')
    def validate_lists_not_empty(cls, v):
        if not v or len(v) == 0:
            raise ValueError("At least one option must be selected")
        return v
    
    @validator('location', 'farm_scale', 'financial_knowledge')
    def validate_required_fields(cls, v):
        if not v or v.strip() == "":
            raise ValueError("This field is required")
        return v
    
    @validator('crop_type', 'livestock_type')
    def validate_optional_text_fields(cls, v):
        # These fields are optional but clean them if provided
        return v.strip() if v else ""

    class Config:
        populate_by_name = True
        json_schema_extra = {
            "example": {
                "agricultural_activity": ["Trồng trọt", "Chăn nuôi"],
                "crop_type": "Lúa, ngô",
                "livestock_type": "Bò, heo",
                "location": "An Giang",
                "farm_scale": "10 đến 25 hecta",
                "support_needs": ["Lời khuyên về kế hoạch phát triển cho canh tác", "Lời khuyên về chọn khoản vay vốn"],
                "financial_knowledge": "Tôi biết và đã sử dụng dịch vụ tài chính"
            }
        }


class UserPreference(BaseModel):
    """
    Model for user preferences stored in preference storage.
    """
    
    user_id: str = Field(
        description="Unique identifier for the user (Primary Key)"
    )
    
    user_email: str = Field(
        description="Email address of the user"
    )
    
    questionnaire_answer: QuestionnaireAnswer = Field(
        description="User's answers to the onboarding questionnaire"
    )
    
    recorded_on: str = Field(
        description="Timestamp when the preference was first recorded"
    )
    
    updated_on: str = Field(
        description="Timestamp when the preference was last updated"
    )
    
    @validator('user_id')
    def validate_user_id(cls, v):
        if not v or v.strip() == "":
            raise ValueError("User ID is required")
        return v
    
    @validator('user_email')
    def validate_user_email(cls, v):
        if not v or "@" not in v:
            raise ValueError("Valid email address is required")
        return v.lower().strip()
    
    @validator('recorded_on', 'updated_on')
    def validate_timestamps(cls, v):
        if not v:
            return datetime.utcnow().isoformat()
        return v

    class Config:
        json_schema_extra = {
            "example": {
                "user_id": "550e8400-e29b-41d4-a716-446655440000",
                "user_email": "farmer@example.com",
                "questionnaire_answer": {
                    "agricultural_activity": ["Trồng trọt", "Chăn nuôi"],
                    "crop_type": "Lúa, ngô",
                    "livestock_type": "Bò, heo",
                    "location": "An Giang",
                    "farm_scale": "10 đến 25 hecta",
                    "support_needs": ["Lời khuyên về kế hoạch phát triển cho canh tác"],
                    "financial_knowledge": "Tôi biết và đã sử dụng dịch vụ tài chính"
                },
                "recorded_on": "2024-01-15T10:30:00Z",
                "updated_on": "2024-01-15T10:30:00Z"
            }
        }


class PreferenceCreateRequest(BaseModel):
    """
    Model for creating new user preferences.
    """
    
    questionnaire_answer: QuestionnaireAnswer = Field(
        description="User's answers to the onboarding questionnaire"
    )

    class Config:
        populate_by_name = True
        json_schema_extra = {
            "example": {
                "questionnaire_answer": {
                    "agricultural_activity": ["Trồng trọt", "Chăn nuôi"],
                    "crop_type": "Lúa, ngô",
                    "livestock_type": "Bò, heo",
                    "location": "An Giang",
                    "farm_scale": "10 đến 25 hecta",
                    "support_needs": ["Lời khuyên về kế hoạch phát triển cho canh tác"],
                    "financial_knowledge": "Tôi biết và đã sử dụng dịch vụ tài chính"
                }
            }
        }


class PreferenceUpdateRequest(BaseModel):
    """
    Model for updating existing user preferences.
    """

    questionnaire_answer: Optional[QuestionnaireAnswer] = Field(
        None,
        description="Updated answers to the onboarding questionnaire"
    )

    class Config:
        populate_by_name = True


class PreferenceResponse(BaseModel):
    """
    Model for preference API responses.
    """
    
    success: bool = Field(description="Whether the operation was successful")
    message: str = Field(description="Response message")
    data: Optional[UserPreference] = Field(None, description="Preference data if applicable")

    class Config:
        json_schema_extra = {
            "example": {
                "success": True,
                "message": "Preferences saved successfully",
                "data": {
                    "user_id": "550e8400-e29b-41d4-a716-446655440000",
                    "user_email": "farmer@example.com",
                    "questionnaire_answer": {
                        "agricultural_activity": ["Trồng trọt"],
                        "crop_type": "Lúa",
                        "livestock_type": "",
                        "location": "An Giang",
                        "farm_scale": "10 đến 25 hecta",
                        "support_needs": ["Lời khuyên về kế hoạch phát triển cho canh tác"],
                        "financial_knowledge": "Tôi biết và đã sử dụng dịch vụ tài chính"
                    },
                    "recorded_on": "2024-01-15T10:30:00Z",
                    "updated_on": "2024-01-15T10:30:00Z"
                }
            }
        }


def convert_to_dynamodb_item(user_preference: UserPreference) -> Dict[str, Any]:
    """
    Convert UserPreference model to preference storage item format.
    """
    questionnaire_dict = user_preference.questionnaire_answer.dict(by_alias=True)
    
    # Convert List fields to JSON strings for DynamoDB storage
    if 'agriculturalActivity' in questionnaire_dict:
        questionnaire_dict['agriculturalActivity'] = json.dumps(questionnaire_dict['agriculturalActivity'])
    if 'supportNeeds' in questionnaire_dict:
        questionnaire_dict['supportNeeds'] = json.dumps(questionnaire_dict['supportNeeds'])
    
    return {
        "user_id": user_preference.user_id,
        "user_email": user_preference.user_email,
        "questionnaire_answer": questionnaire_dict,
        "recorded_on": user_preference.recorded_on,
        "updated_on": user_preference.updated_on
    }


def convert_from_dynamodb_item(item: Dict[str, Any]) -> UserPreference:
    """
    Convert preference storage item to UserPreference model.
    """
    questionnaire_data = item["questionnaire_answer"].copy()
    
    # Convert JSON strings back to Lists for List fields
    if 'agriculturalActivity' in questionnaire_data and isinstance(questionnaire_data['agriculturalActivity'], str):
        try:
            questionnaire_data['agriculturalActivity'] = json.loads(questionnaire_data['agriculturalActivity'])
        except (json.JSONDecodeError, TypeError):
            questionnaire_data['agriculturalActivity'] = []
    
    if 'supportNeeds' in questionnaire_data and isinstance(questionnaire_data['supportNeeds'], str):
        try:
            questionnaire_data['supportNeeds'] = json.loads(questionnaire_data['supportNeeds'])
        except (json.JSONDecodeError, TypeError):
            questionnaire_data['supportNeeds'] = []
    
    return UserPreference(
        user_id=item["user_id"],
        user_email=item["user_email"],
        questionnaire_answer=QuestionnaireAnswer(**questionnaire_data),
        recorded_on=item["recorded_on"],
        updated_on=item["updated_on"]
    )


# Available options for validation (matching frontend options)
AGRICULTURAL_ACTIVITIES = [
    'Trồng trọt',
    'Chăn nuôi', 
    'Thủy sản',
    'Lâm nghiệp',
    'Nông nghiệp hữu cơ',
    'Chế biến nông sản'
]

FARM_SCALES = [
    '0 đến 10 hecta',
    '10 đến 25 hecta', 
    '25 đến 50 hecta',
    '50 đến 100 hecta',
    '>100 hecta'
]

SUPPORT_NEEDS_OPTIONS = [
    'Lời khuyên về kế hoạch phát triển cho canh tác',
    'Lời khuyên về chọn khoản vay vốn',
    'Học kiến thức tài chính chung',
    'Lời khuyên về quản lí tài chính',
    'Cập nhật xu hướng thị trường và định hướng bán ra'
]

FINANCIAL_KNOWLEDGE_OPTIONS = [
    'Tôi hoàn toàn không biết',
    'Tôi biết một số dịch vụ tài chính nhưng chưa sử dụng bao giờ',
    'Tôi biết và đã sử dụng dịch vụ tài chính',
    'Tôi biết sâu và đã sử dụng các dịch vụ tài chính thường xuyên'
]

VIETNAM_LOCATIONS = [
    'An Giang', 'Bà Rịa - Vũng Tàu', 'Bắc Giang', 'Bắc Kạn', 'Bạc Liêu', 'Bắc Ninh',
    'Bến Tre', 'Bình Định', 'Bình Dương', 'Bình Phước', 'Bình Thuận', 'Cà Mau',
    'Cao Bằng', 'Đắk Lắk', 'Đắk Nông', 'Điện Biên', 'Đồng Nai', 'Đồng Tháp',
    'Gia Lai', 'Hà Giang', 'Hà Nam', 'Hà Tĩnh', 'Hải Dương', 'Hậu Giang',
    'Hòa Bình', 'Hưng Yên', 'Khánh Hòa', 'Kiên Giang', 'Kon Tum', 'Lai Châu',
    'Lâm Đồng', 'Lạng Sơn', 'Lào Cai', 'Long An', 'Nam Định', 'Nghệ An',
    'Ninh Bình', 'Ninh Thuận', 'Phú Thọ', 'Quảng Bình', 'Quảng Nam', 'Quảng Ngãi',
    'Quảng Ninh', 'Quảng Trị', 'Sóc Trăng', 'Sơn La', 'Tây Ninh', 'Thái Bình',
    'Thái Nguyên', 'Thanh Hóa', 'Thừa Thiên Huế', 'Tiền Giang', 'Trà Vinh',
    'Tuyên Quang', 'Vĩnh Long', 'Vĩnh Phúc', 'Yên Bái', 'Phú Yên', 'Cần Thơ',
    'Đà Nẵng', 'Hải Phòng', 'Hà Nội', 'TP. Hồ Chí Minh'
]
