from apps.portfolio.core.domain.entities import PortfolioItemEntity
from apps.portfolio.core.domain.repositories import IPortfolioRepository

class UploadPortfolioItemUseCase:
    def __init__(self, portfolio_repo: IPortfolioRepository):
        self.portfolio_repo = portfolio_repo

    def execute(self, teacher_id: int, item_type: str, title: str, description: str, file_path: str) -> PortfolioItemEntity:
        
        if item_type not in ['TRABAJO', 'TAREA']:
            raise ValueError("El tipo de ficha debe ser 'TRABAJO' o 'TAREA'.")
            
        item = PortfolioItemEntity(
            id=None,
            teacher_id=teacher_id,
            item_type=item_type,
            title=title,
            description=description,
            file_path=file_path
        )
        
        return self.portfolio_repo.save(item)