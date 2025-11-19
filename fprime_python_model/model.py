from typing import Dict, List
from fprime_python_model.fpp_ast.fpp_ast_node import AstNode, AstId
from fprime_python_model.fpp_ast.fpp_ast import Annotated
from fprime_python_model.translators.ast_translator import translate_ast_json
from fprime_python_model.translators.loc_map_translator import (
    translate_location_map_json,
)
from fprime_python_model.translators.analysis_translator import AnalysisTranslator
from fprime_python_model.translators.construct_ast_id_map import ConstructAstMap
from fprime_python_model.fpp_ast.fpp_ast import TransUnit
from fprime_python_model.fpp_ast.fpp_locations import Location
from fprime_python_model.semantics.analysis import Analysis


class FprimePythonModel:

    def __init__(
        self,
        fpp_ast_json_file: str,
        fpp_locations_json_file: str,
        fpp_analysis_json_file: str,
    ):
        self.fpp_ast_json_file = fpp_ast_json_file
        self.fpp_locations_json_file = fpp_locations_json_file
        self.fpp_analysis_json_file = fpp_analysis_json_file
        self._ast_id_map: Dict[AstId, AstNode] = dict()
        self._annotated_ast_id_map: Dict[AstId, Annotated[AstNode]] = dict()
        self._ast: List[TransUnit] = list()
        self._location_map: Dict[int, Location] = dict()
        self._analysis: Analysis = Analysis()

        self._load()

    def _load(self):
        self._location_map = translate_location_map_json(self.fpp_locations_json_file)
        self._ast = translate_ast_json(self.fpp_ast_json_file)
        self._ast_id_map, self._annotated_ast_id_map = (
            ConstructAstMap().construct_ast_map(self._ast)
        )
        self._analysis = AnalysisTranslator(
            self._ast_id_map, self._annotated_ast_id_map, self.fpp_analysis_json_file
        ).translate_analysis_json()

    @property
    def analysis(self) -> Analysis:
        return self._analysis

    @property
    def ast(self) -> List[TransUnit]:
        return self._ast

    @property
    def location_map(self) -> Dict[int, Location]:
        return self._location_map

    @property
    def annotated_ast_id_map(self) -> Dict[AstId, Annotated[AstNode]]:
        return self._annotated_ast_id_map

    @property
    def ast_id_map(self) -> Dict[AstId, AstNode]:
        return self._ast_id_map

    def get_location(self, node: AstNode) -> Location:
        return self.location_map[node._id]
