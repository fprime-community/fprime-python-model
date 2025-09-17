from typing import Dict, List
from fprime_python_model.fpp_ast.fpp_ast_node import AstNode, AstId, T
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
        self.ast_id_map: Dict[AstId, AstNode[T]] = dict()
        self.annotated_ast_id_map: Dict[AstId, Annotated[AstNode[T]]] = dict()
        self.ast: List[TransUnit] = list()
        self.location_map: Dict[int, Location] = dict()
        self.analysis: Analysis = Analysis()

        self._translate_json()

    def _translate_json(self):
        self.location_map = translate_location_map_json(self.fpp_locations_json_file)
        self.ast = translate_ast_json(self.fpp_ast_json_file)
        self.ast_id_map, self.annotated_ast_id_map = (
            ConstructAstMap().construct_ast_map(self.ast)
        )
        self.analysis = AnalysisTranslator(
            self.ast_id_map, self.annotated_ast_id_map, self.fpp_analysis_json_file
        ).translate_analysis_json()
