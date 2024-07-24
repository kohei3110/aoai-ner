from pydantic import BaseModel


class InquiryRequest(BaseModel):
    text: str