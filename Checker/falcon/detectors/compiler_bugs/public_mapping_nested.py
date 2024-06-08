"""
Module detecting public mappings with nested variables (returns incorrect values prior to 0.5.x)
"""

from falcon.detectors.abstract_detector import AbstractDetector, DetectorClassification
from falcon.core.solidity_types.mapping_type import MappingType
from falcon.core.solidity_types.user_defined_type import UserDefinedType
from falcon.core.declarations.structure import Structure


def detect_public_nested_mappings(contract):
    """
    Detect any state variables that are initialized from an immediate function call (prior to constructor run).
    :param contract: The contract to detect state variable definitions for.
    :return: A list of all state variables defined in the given contract that meet the specified criteria.
    """
    results = []

    for state_variable in contract.variables:
        # Verify this variable is defined in this contract
        if state_variable.contract != contract:
            continue

        # Verify this is a public mapping
        if state_variable.visibility != "public" or not isinstance(
            state_variable.type, MappingType
        ):
            continue

        # Verify the value type is a user defined type (struct)
        if not isinstance(state_variable.type.type_to, UserDefinedType) or not isinstance(
            state_variable.type.type_to.type, Structure
        ):
            continue

        # Obtain the struct
        struct_type = state_variable.type.type_to.type
        for struct_member in struct_type.elems.values():
            if isinstance(struct_member.type, UserDefinedType) and isinstance(
                struct_member.type.type, Structure
            ):
                results.append(state_variable)
                break

    return results


class PublicMappingNested(AbstractDetector):
    """
    Detects public mappings with nested variables (returns incorrect values prior to 0.5.x)
    """

    ARGUMENT = "structure-in-mappings"
    HELP = "Public mappings with nested variables"
    IMPACT = DetectorClassification.HIGH
    CONFIDENCE = DetectorClassification.HIGH

    WIKI = " "

    WIKI_TITLE = "Public mappings with nested variables"
    WIKI_DESCRIPTION = "Prior to Solidity 0.5, a public mapping with nested structures returned [incorrect values](https://github.com/ethereum/solidity/issues/5520)."
    WIKI_EXPLOIT_SCENARIO = """Bob interacts with a contract that has a public mapping with nested structures. The values returned by the mapping are incorrect, breaking Bob's usage"""
    WIKI_RECOMMENDATION = "Do not use public mapping with nested structures."

    def _detect(self):
        """
        Detect public mappings with nested variables (returns incorrect values prior to 0.5.x)

        Returns:
            list: {'vuln', 'filename,'contract','func', 'public_nested_mappings'}

        """
        results = []

        if self.compilation_unit.solc_version and self.compilation_unit.solc_version >= "0.5.0":
            return []

        if self.compilation_unit.solc_version and self.compilation_unit.solc_version.startswith(
            "0.5."
        ):
            return []

        for contract in self.contracts:
            public_nested_mappings = detect_public_nested_mappings(contract)
            if public_nested_mappings:
                for public_nested_mapping in public_nested_mappings:
                    info = [public_nested_mapping, " is a public mapping with nested variables\n"]
                    json = self.generate_result(info)
                    results.append(json)

        return results
