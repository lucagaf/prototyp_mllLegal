from typing import List, Dict, Any

class RetrievedClause:
    def __init__(self, clause_name, clause_subname, input_clause):
        """
        Stores the input clause and metadata.

        Parameters:
        - clause_name (str): The main clause category.
        - clause_subname (str): The specific clause identifier.
        - input_clause (str): The queried clause.
        """
        self.clause_name = clause_name
        self.clause_subname = clause_subname
        self.input_clause = input_clause
        self.retrieved_clauses: List[Dict[str, float]] = []  # List of (clause, confidence) tuples
        self.answer = None
        self.modified_clause = None

    def display_retrievedClauses(self, top_n=1):
        """Prints the top N retrieved clauses with confidence scores."""
        print(f"Top {top_n} retrieved clauses:")
        for i, (clause, confidence) in enumerate(self.retrieved_clauses[:top_n], 1):
            print(f"{i}. Confidence: {confidence:.4f}")
            print(clause)
            print("-----")

    def return_retrievedClauses(self, top_n=3):
        """Returns the retrieved clauses."""
        result = []
        result.append(f"Top {top_n} retrieved clauses:")

        for i, (clause, confidence) in enumerate(self.retrieved_clauses[:top_n], 1):
            result.append(f"{i}. Confidence: {confidence:.4f}")
            result.append(clause)
            result.append("-----")

        return "\n".join(result)

    def display(self):
        """Helper function to display the RetrievedClause object."""
        print(f"Clause Name: {self.clause_name}")
        print(f"Clause Subname: {self.clause_subname}")
        print(f"Input Clause: {self.input_clause}")
        print(f"Retrieved Clauses: {self.retrieved_clauses}")
        print(f"Answer: {self.answer}")
        return self

    def add_clause(self, clause: Dict[str, float]) -> None:
        """Adds a single clause to the contract."""
        self.retrieved_clauses.append(clause)

    def set_clauses(self, clauses: List[Dict[str, float]]) -> None:
        """Sets all clauses at once."""
        self.retrieved_clauses = clauses

    def get_clauses(self) -> List[Dict[str, float]]:
        """Returns the list of retrieved clauses."""
        return self.retrieved_clauses

    def get_best_clause(self) -> str:
        """
        Returns the clause with the highest confidence.
        If no clauses are available, returns an Error.
        """
        if not self.retrieved_clauses:
            raise Exception(f"No retrieved clauses found for {self.clause_name}")

        best_entry = max(self.retrieved_clauses, key=lambda entry: entry['confidence'])
        return best_entry['clause']

    def __str__(self) -> str:
        """Returns a human-friendly string representation of the contract."""
        if not self.retrieved_clauses:
            return "Contract with no retrieved clauses."
        output = "Contract with the following retrieved clauses:\n"
        for i, clause_info in enumerate(self.retrieved_clauses, start=1):
            clause_text = clause_info.get('clause', '')
            confidence = clause_info.get('confidence', 'N/A')
            output += f"\nClause {i}:\n"
            output += f"  Retrieved Clause:  {clause_text}\n"
            output += f"  Confidence: {confidence}\n"
        return output

    def __repr__(self):
        return (
            f"RetrievedClause(\n"
            f"  clause_name: {self.clause_name},\n"
            f"  clause_subname: {self.clause_subname},\n"
            f"  input_clause: {self.input_clause},\n"
            f"  retrieved_clauses: {self.retrieved_clauses},\n"
            f"  answer: {self.answer},\n"
            f"  modified_clause: {self.modified_clause}\n"
            f")"
        )