from django.urls.base import reverse
from django.utils.translation import gettext_lazy as _
from enum import Enum
from webook.crumbinator.crumb_node import CrumbNode


class SectionCrudlPathMap:
    def __init__(self, detail_url: str, create_url: str, edit_url: str, delete_url: str, list_url: str) -> None:
        self.detail_url = detail_url
        self.create_url = create_url
        self.edit_url = edit_url
        self.delete_url = delete_url
        self.list_url = list_url

    create_url = None
    edit_url = None
    delete_url = None
    list_url = None


class SectionManifest:
	def __init__(self, 
		section_title: str,
		section_icon: str,
		section_crumb_url: str,
		crudl_map=None):
		
		self.section_title = section_title
		self.section_icon = section_icon
		self.section_crumb_url = section_crumb_url
		self.crudl_map = crudl_map

	def get_crumb_node(self):
		return CrumbNode(
			title=self.section_title,
			icon_class=self.section_icon,
			url=self.section_crumb_url,
			is_active=False,
		)


class SUBTITLE_MODE(Enum):
	TITLE_AS_SUBTITLE = 0,
	ENTITY_NAME_AS_SUBTITLE = 1


class ViewMeta:
	def __init__(self,
		subtitle: str,
		current_crumb_title:str,
		current_crumb_icon: str=None,
		entity_name_attribute:str=None,
		subtitle_mode: SUBTITLE_MODE = SUBTITLE_MODE.TITLE_AS_SUBTITLE,
		subtitle_prefix: str=None):
					
		self.subtitle = subtitle
		self.subtitle_prefix = subtitle_prefix
		self.current_crumb_icon = current_crumb_icon
		self.current_crumb_title = current_crumb_title
		self.subtitle_mode = subtitle_mode
	
	def get_crumb_node(self):
		return CrumbNode(
			title=self.current_crumb_title,
			url="", # url intentionally blank - this is active node, so not needed
			icon_class=self.current_crumb_icon,
			is_active=True,
		)

	class Preset:
		@staticmethod
		def detail(entity_class):
			"""
				Get a view meta preset for the detail view, using application standards
				Please note that the model must implement the plurality/naming mixin

				:param entity_class: The class of the model the view is concerned with
				:type entity_class: The model.
			"""
			name = f"{_('View')} {entity_class.Meta.verbose_name}"
			return ViewMeta(
				current_crumb_icon="fas fa-eye",
				subtitle=name,
				current_crumb_title=name,
				subtitle_mode=SUBTITLE_MODE.ENTITY_NAME_AS_SUBTITLE
			)
		
		@staticmethod
		def create(entity_class):
			"""
				Get a view meta preset for the create view, using application standards.
				Please note that the model must implement the plurality/naming mixin
				
				:param entity_class: The class of the model the view is concerned with
				:type entity_class: The model.
			"""
			name = f"{_('Create')} {entity_class.Meta.verbose_name}"
			return ViewMeta(
				current_crumb_icon="fas fa-plus",
				subtitle=name,
				current_crumb_title=name,
			)
			
		@staticmethod
		def delete(entity_class):
			"""
				Get a view meta preset for the delete view, using application standards.
				Please note that the model must implement the plurality/naming mixin
				
				:param entity_class: The class of the model the view is concerned with
				:type entity_class: The model.
			"""
			name = f"{_('Delete')} {entity_class.Meta.verbose_name}"
			return ViewMeta(
				current_crumb_icon="fas fa-trash",
				subtitle=name,
				current_crumb_title=name,
			)
			
		@staticmethod
		def edit(entity_class):
			"""
				Get a view meta preset for the edit view, using application standards.
				Please note that the model must implement the plurality/naming mixin
				
				:param entity_class: The class of the model the view is concerned with
				:type entity_class: The model.
			"""
			name = f"{_('Edit')} {entity_class.Meta.verbose_name}"
			return ViewMeta(
				current_crumb_icon="fas fa-edit",
				subtitle=name,
				current_crumb_title=name,
			)
			
		@staticmethod
		def table(entity_class):
			"""
				Get a view meta preset for the list view, using application standards.
				Please note that the model must implement the plurality/naming mixin
				
				:param entity_class: The class of the model the view is concerned with
				:type entity_class: The model.
			"""
			name = f"{_('All')} {entity_class.Meta.verbose_name}"
			return ViewMeta(
				current_crumb_icon="fas fa-list",
				subtitle=name,
				current_crumb_title=name,
			)
			