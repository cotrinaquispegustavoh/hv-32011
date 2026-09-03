from typing import List
from apps.portfolio.core.domain.entities import PortfolioItemEntity, ObservationEntity
from apps.portfolio.core.domain.repositories import IPortfolioRepository, IObservationRepository
from apps.portfolio.infrastructure.models import PortfolioItem, Observation

class DjangoPortfolioRepository(IPortfolioRepository):
    def _to_entity(self, model: PortfolioItem) -> PortfolioItemEntity:
        observations = [
            ObservationEntity(
                id=obs.id, portfolio_item_id=obs.portfolio_item_id, director_id=obs.director_id,
                content=obs.content, created_at=obs.created_at
            ) for obs in model.observations.all()
        ]
        return PortfolioItemEntity(
            id=model.id, teacher_id=model.teacher_id,
            section_id=model.section_id,
            section_name=model.section.display_name if model.section else "General",
            item_type=model.item_type, title=model.title, description=model.description,
            file_path=model.file.name if model.file else "", created_at=model.created_at,
            observations=observations,
            teacher_name=f"{model.teacher.last_name}, {model.teacher.first_name}" # <-- NUEVO
        )

    def save(self, item: PortfolioItemEntity) -> PortfolioItemEntity:
        model, _ = PortfolioItem.objects.update_or_create(
            id=item.id,
            defaults={
                'teacher_id': item.teacher_id,
                'section_id': item.section_id,
                'item_type': item.item_type,
                'title': item.title,
                'description': item.description,
            }
        )
        if item.file_path and not model.file:
            model.file = item.file_path
            model.save()
            
        item.id = model.id
        item.created_at = model.created_at
        return item

    def get_by_teacher(self, teacher_id: int) -> List[PortfolioItemEntity]:
        models = PortfolioItem.objects.filter(teacher_id=teacher_id).select_related('teacher', 'section').prefetch_related('observations').order_by('-created_at')
        return [self._to_entity(m) for m in models]

    def get_all(self) -> List[PortfolioItemEntity]:
        # Optimizamos con select_related para evitar consultas N+1
        models = PortfolioItem.objects.all().select_related('teacher', 'section').prefetch_related('observations').order_by('-created_at')
        return [self._to_entity(m) for m in models]

    def get_by_section(self, section_id: int) -> List[PortfolioItemEntity]:
        models = PortfolioItem.objects.filter(section_id=section_id).select_related('teacher', 'section').prefetch_related('observations').order_by('-created_at')
        return [self._to_entity(m) for m in models]

class DjangoObservationRepository(IObservationRepository):
    def save(self, observation: ObservationEntity) -> ObservationEntity:
        model, _ = Observation.objects.update_or_create(
            id=observation.id,
            defaults={
                'portfolio_item_id': observation.portfolio_item_id,
                'director_id': observation.director_id,
                'content': observation.content
            }
        )
        observation.id = model.id
        observation.created_at = model.created_at
        return observation
