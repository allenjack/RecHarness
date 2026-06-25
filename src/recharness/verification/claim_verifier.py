"""Pattern-based product claim verification."""

from __future__ import annotations

from recharness.schema import ProductItem


class ClaimVerifier:
    """Check high-signal recommendation claims against catalog attributes."""

    def verify_claims(self, product: ProductItem, agent_answer: str) -> list[str]:
        answer = agent_answer.lower()
        unsupported: list[str] = []

        if "waterproof" in answer:
            water_resistance = str(product.attributes.get("water_resistance", "unknown"))
            if water_resistance.lower() != "waterproof":
                unsupported.append(
                    f"{product.title}: waterproof claim is unsupported; "
                    f"catalog water_resistance={water_resistance}"
                )

        return unsupported
