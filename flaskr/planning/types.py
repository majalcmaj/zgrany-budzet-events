from dataclasses import dataclass
from enum import Enum
from typing import Optional


class PlanningStatus(Enum):
    NOT_STARTED = "planning_not_started"
    IN_PROGRESS = "planning_in_progress"
    IN_REVIEW = "in_review_by_minister"
    NEEDS_CORRECTION = "needs_correction"
    FINISHED = "finished"


class ExpensesStatus(Enum):
    NOT_STARTED = "not_started"
    IN_PROGRESS = "in_progress"
    CLOSED = "closed"


@dataclass
class Expense:
    chapter: int | str
    task_name: str
    financial_needs: int
    role: str
    # Additional fields from Excel
    czesc: Optional[int] = None  # część
    departament: Optional[str] = None  # departament
    rodzaj_projektu: Optional[str] = None  # rodzaj projektu
    opis_projektu: Optional[str] = None  # opis projektu
    data_zlozenia: Optional[str] = None  # DATA ZŁOŻENIA WNIOSKU
    program_operacyjny: Optional[str] = None  # PROGRAM OPERACYJNY/INICJATYWA
    termin_realizacji: Optional[str] = None  # termin realizacji
    zrodlo_fin: Optional[int] = None  # źródło fin.
    bz: Optional[str] = None  # bz
    beneficjent: Optional[str] = None  # Beneficjent
    szczegolowe_uzasadnienie: Optional[str] = None  # Szczegółowe uzasadnienie
    budget_2025: Optional[int] = None  # 2025
    budget_2026: Optional[int] = None  # 2026
    budget_2027: Optional[int] = None  # 2027
    budget_2028: Optional[int] = None  # 2028
    budget_2029: Optional[int] = None  # 2029
    etap_dzialan: Optional[str] = None  # etap działań
    umowy: Optional[str] = None  # umowy
    nr_umowy: Optional[str] = None  # nr umowy
    z_kim_zawarta: Optional[str] = None  # z kim zawarta
    uwagi: Optional[str] = None  # Uwagi
