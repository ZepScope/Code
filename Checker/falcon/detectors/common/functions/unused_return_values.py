"""
Module detecting unused return values from external calls
"""

from falcon.core.variables.state_variable import StateVariable
from falcon.detectors.abstract_detector import AbstractDetector, DetectorClassification
from falcon.ir.operations import HighLevelCall
from falcon.core.declarations import Function
from falcon.core.cfg.node import NodeType


class UnusedReturnValues(AbstractDetector):
    """
    If the return value of a function is never used, it's likely to be bug
    """

    ARGUMENT = "unused-return"
    HELP = "Unused return values"
    IMPACT = DetectorClassification.MEDIUM
    CONFIDENCE = DetectorClassification.MEDIUM

    WIKI = " "

    WIKI_TITLE = "Unused return"
    WIKI_DESCRIPTION = (
        "The return value of an external call is not stored in a local or state variable."
    )

    # region wiki_exploit_scenario
    WIKI_EXPLOIT_SCENARIO = """
```solidity
contract MyConc{
    using SafeMath for uint;   
    function my_func(uint a, uint b) public{
        a.add(b);
    }
}
```
`MyConc` calls `add` of `SafeMath`, but does not store the result in `a`. As a result, the computation has no effect."""
    # endregion wiki_exploit_scenario

    WIKI_RECOMMENDATION = "Ensure that all the return values of the function calls are used."

    def _is_instance(self, ir):  # pylint: disable=no-self-use
        return isinstance(ir, HighLevelCall) and (
            (
                isinstance(ir.function, Function)
                and ir.function.solidity_signature
                not in ["transfer(address,uint256)", "transferFrom(address,address,uint256)"]
            )
            or not isinstance(ir.function, Function)
        )

    def detect_unused_return_values(self, f):  # pylint: disable=no-self-use
        """
            Return the nodes where the return value of a call is unused
        Args:
            f (Function)
        Returns:
            list(Node)
        """
        values_returned = []
        nodes_origin = {}
        for n in f.nodes:
            if n.type == NodeType.TRY:
                continue
            for ir in n.irs:
                if self._is_instance(ir):
                    # if a return value is stored in a state variable, it's ok
                    if ir.lvalue and not isinstance(ir.lvalue, StateVariable):
                        values_returned.append(ir.lvalue)
                        nodes_origin[ir.lvalue] = ir
                for read in ir.read:
                    if read in values_returned:
                        values_returned.remove(read)

        return [nodes_origin[value].node for value in values_returned]

    def _detect(self):
        """Detect high level calls which return a value that are never used"""
        results = []
        info=[]
        for c in self.compilation_unit.contracts:
            for f in c.functions + c.modifiers:
                if f.contract_declarer != c:
                    continue
                unused_return = self.detect_unused_return_values(f)
                if unused_return:
                    for node in unused_return:
                        info.append(self.generate_result([f, "have ignores return value in ", node, "\n"]))
        results.extend(info) if info else None

        return results
