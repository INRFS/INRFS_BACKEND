from decimal import Decimal
from typing import Optional

from pydantic import BaseModel, ConfigDict


class AccountTypeResponse(BaseModel):
    id: int
    account_type_name: str
    is_active: Optional[bool] = True

    model_config = ConfigDict(from_attributes=True)


class InterestRateResponse(BaseModel):
    id: int
    monthly_interest_rate: Decimal
    is_active: Optional[bool] = True

    model_config = ConfigDict(from_attributes=True)


class InvestmentStatusResponse(BaseModel):
    id: int
    status_name: str
    is_active: Optional[bool] = True

    model_config = ConfigDict(from_attributes=True)


class InvestmentTenureResponse(BaseModel):
    id: int
    tenure_months: int
    is_active: Optional[bool] = True

    model_config = ConfigDict(from_attributes=True)


class InvestorRequestStatusResponse(BaseModel):
    id: int
    status_name: str
    is_active: Optional[bool] = True

    model_config = ConfigDict(from_attributes=True)


class KycStatusResponse(BaseModel):
    id: int
    kyc_status_name: str
    is_active: Optional[bool] = True

    model_config = ConfigDict(from_attributes=True)


class PaymentMethodResponse(BaseModel):
    id: int
    payment_method_name: str
    is_active: Optional[bool] = True

    model_config = ConfigDict(from_attributes=True)


class PaymentStatusResponse(BaseModel):
    id: int
    payment_status_name: str
    is_active: Optional[bool] = True

    model_config = ConfigDict(from_attributes=True)


class RoleResponse(BaseModel):
    id: int
    role_name: str
    is_active: Optional[bool] = True

    model_config = ConfigDict(from_attributes=True)


class SettlementStatusResponse(BaseModel):
    id: int
    status_name: str
    is_active: Optional[bool] = True

    model_config = ConfigDict(from_attributes=True)


class StateResponse(BaseModel):
    id: int
    state_name: str
    is_active: Optional[bool] = True

    model_config = ConfigDict(from_attributes=True)


class UserStatusResponse(BaseModel):
    id: int
    status_name: str
    is_active: Optional[bool] = True

    model_config = ConfigDict(from_attributes=True)


class BranchResponse(BaseModel):
    id: int
    branch_name: str
    state_id: int
    is_active: Optional[bool] = True

    model_config = ConfigDict(from_attributes=True)


class AllMastersResponse(BaseModel):
    account_types: list[AccountTypeResponse]
    interest_rates: list[InterestRateResponse]
    investment_statuses: list[InvestmentStatusResponse]
    investment_tenures: list[InvestmentTenureResponse]
    investor_request_statuses: list[InvestorRequestStatusResponse]
    kyc_statuses: list[KycStatusResponse]
    payment_methods: list[PaymentMethodResponse]
    payment_statuses: list[PaymentStatusResponse]
    roles: list[RoleResponse]
    settlement_statuses: list[SettlementStatusResponse]
    states: list[StateResponse]
    user_statuses: list[UserStatusResponse]
    branches: list[BranchResponse]