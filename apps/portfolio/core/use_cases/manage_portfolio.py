from typing import List
from apps.portfolio.core.domain.entities import PortfolioItemEntity, ObservationEntity
from apps.portfolio.core.domain.repositories import IPortfolioRepository, IObservationRepository

class UploadPortfolioItemUseCase:
    def __init__(self, portfolio_repo: IPortfolioRepository):
        self.portfolio_repo = portfolio_repo

    def execute(self, teacher_id: int, item_type: str, title: str, description: str, file_path: str) -> PortfolioItemEntity:
        if item_type not in ['TRABAJO', 'TAREA']:
            raise ValueError("El tipo de ficha debe ser 'TRABAJO' o 'TAREA'.")
            
        item = PortfolioItemEntity(
            id=None, teacher_id=teacher_id, section_id=None, section_name=None,
            item_type=item_type, title=title, description=description,
            file_path=file_path
        )
        return self.portfolio_repo.save(item)

# --- NUEVOS CASOS DE USO ---
class GetAllPortfolioItemsUseCase:
    def __init__(self, portfolio_repo: IPortfolioRepository):
        self.portfolio_repo = portfolio_repo

    def execute(self) -> List[PortfolioItemEntity]:
        return self.portfolio_repo.get_all()

class AddObservationUseCase:
    def __init__(self, observation_repo: IObservationRepository):
        self.observation_repo = observation_repo

    def execute(self, portfolio_item_id: int, director_id: int, content: str) -> ObservationEntity:
        if not content.strip():
            raise ValueError("La observación no puede estar vacía.")
            
        obs = ObservationEntity(
            id=None,
            portfolio_item_id=portfolio_item_id,
            director_id=director_id,
            content=content
        )
        return self.observation_repo.save(obs)