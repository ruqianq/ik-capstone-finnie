from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from typing import Dict


class TaxEducationAgent:
    """
    Agent for tax education, including tax-advantaged accounts,
    capital gains, and tax strategies for investors.
    """

    def __init__(self):
        self.llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)

        # Tax knowledge base (embedded for quick reference)
        self.tax_knowledge = {
            "401k": {
                "name": "401(k)",
                "type": "Employer-sponsored retirement account",
                "contribution_limit_2024": "$23,000 ($30,500 if 50+)",
                "tax_treatment": "Pre-tax contributions, taxed on withdrawal",
                "key_features": [
                    "Employer matching (free money!)",
                    "Reduces taxable income",
                    "Required Minimum Distributions (RMDs) at 73",
                    "10% penalty for early withdrawal before 59½"
                ]
            },
            "roth_401k": {
                "name": "Roth 401(k)",
                "type": "Employer-sponsored retirement account",
                "contribution_limit_2024": "$23,000 ($30,500 if 50+)",
                "tax_treatment": "After-tax contributions, tax-free withdrawals",
                "key_features": [
                    "No income limits (unlike Roth IRA)",
                    "Tax-free growth and withdrawals in retirement",
                    "Good if you expect higher taxes in retirement",
                    "Subject to RMDs (unlike Roth IRA)"
                ]
            },
            "traditional_ira": {
                "name": "Traditional IRA",
                "type": "Individual Retirement Account",
                "contribution_limit_2024": "$7,000 ($8,000 if 50+)",
                "tax_treatment": "May be tax-deductible, taxed on withdrawal",
                "key_features": [
                    "Anyone with earned income can contribute",
                    "Deductibility depends on income and workplace plan",
                    "RMDs required at 73",
                    "10% early withdrawal penalty before 59½"
                ]
            },
            "roth_ira": {
                "name": "Roth IRA",
                "type": "Individual Retirement Account",
                "contribution_limit_2024": "$7,000 ($8,000 if 50+)",
                "tax_treatment": "After-tax contributions, tax-free withdrawals",
                "income_limits_2024": "Phase-out: $146K-$161K (single), $230K-$240K (married)",
                "key_features": [
                    "Tax-free growth and withdrawals",
                    "No RMDs during owner's lifetime",
                    "Contributions (not earnings) can be withdrawn anytime",
                    "Best for those expecting higher future taxes"
                ]
            },
            "hsa": {
                "name": "Health Savings Account (HSA)",
                "type": "Health-related tax-advantaged account",
                "contribution_limit_2024": "$4,150 (individual), $8,300 (family)",
                "tax_treatment": "Triple tax advantage",
                "key_features": [
                    "Pre-tax contributions",
                    "Tax-free growth",
                    "Tax-free withdrawals for medical expenses",
                    "After 65, can withdraw for any purpose (taxed like IRA)",
                    "Requires High Deductible Health Plan (HDHP)"
                ]
            },
            "529": {
                "name": "529 Plan",
                "type": "Education savings account",
                "contribution_limit_2024": "Varies by state, up to $18,000/year gift tax free",
                "tax_treatment": "After-tax contributions, tax-free for education",
                "key_features": [
                    "Tax-free growth for qualified education expenses",
                    "Can transfer to family members",
                    "New: Up to $35K can be rolled to Roth IRA",
                    "10% penalty on earnings for non-qualified withdrawals"
                ]
            }
        }

        self.capital_gains_rates = {
            "short_term": "Taxed as ordinary income (10%-37% based on bracket)",
            "long_term": {
                "0%": "Single: $0-$47,025 | Married: $0-$94,050",
                "15%": "Single: $47,026-$518,900 | Married: $94,051-$583,750",
                "20%": "Above those thresholds"
            },
            "niit": "3.8% Net Investment Income Tax for high earners"
        }

    def process_query(self, query: str) -> str:
        """
        Routes tax-related queries to appropriate responses.
        """
        query_lower = query.lower()

        # Account-specific queries
        if "401k" in query_lower or "401(k)" in query_lower:
            if "roth" in query_lower:
                return self._format_account_info("roth_401k")
            return self._format_account_info("401k")

        if "ira" in query_lower:
            if "roth" in query_lower:
                return self._format_account_info("roth_ira")
            if "traditional" in query_lower or "trad" in query_lower:
                return self._format_account_info("traditional_ira")
            # Compare both
            return self._compare_accounts("traditional_ira", "roth_ira")

        if "hsa" in query_lower or "health savings" in query_lower:
            return self._format_account_info("hsa")

        if "529" in query_lower or "education" in query_lower:
            return self._format_account_info("529")

        # Capital gains queries
        if any(k in query_lower for k in ["capital gain", "gains tax", "selling stock"]):
            return self._explain_capital_gains()

        # Tax-loss harvesting
        if any(k in query_lower for k in ["tax loss", "harvesting", "wash sale"]):
            return self._explain_tax_loss_harvesting()

        # Compare accounts
        if "compare" in query_lower or "vs" in query_lower or "versus" in query_lower:
            return self._compare_all_accounts()

        # Contribution limits
        if "limit" in query_lower or "contribute" in query_lower:
            return self._show_contribution_limits()

        # General tax question - use LLM
        return self._answer_tax_question(query)

    def _format_account_info(self, account_key: str) -> str:
        """
        Formats account information into a readable response.
        """
        account = self.tax_knowledge.get(account_key)
        if not account:
            return "Account information not found."

        report = [f"**{account['name']}**\n"]
        report.append(f"**Type**: {account['type']}")
        report.append(f"**2024 Contribution Limit**: {account['contribution_limit_2024']}")
        report.append(f"**Tax Treatment**: {account['tax_treatment']}")

        if 'income_limits_2024' in account:
            report.append(f"**Income Limits (2024)**: {account['income_limits_2024']}")

        report.append("\n**Key Features**:")
        for feature in account['key_features']:
            report.append(f"- {feature}")

        report.append("\n*This is for educational purposes only. Consult a tax professional for personalized advice.*")
        return "\n".join(report)

    def _explain_capital_gains(self) -> str:
        """
        Explains capital gains tax rules.
        """
        report = ["**Capital Gains Tax Guide**\n"]

        report.append("**Short-Term Capital Gains** (held < 1 year):")
        report.append(f"- {self.capital_gains_rates['short_term']}")

        report.append("\n**Long-Term Capital Gains** (held > 1 year):")
        for rate, threshold in self.capital_gains_rates['long_term'].items():
            report.append(f"- **{rate}**: {threshold}")

        report.append(f"\n**NIIT**: {self.capital_gains_rates['niit']}")

        report.append("\n**Key Strategies**:")
        report.append("- Hold investments > 1 year for lower rates")
        report.append("- Consider tax-loss harvesting to offset gains")
        report.append("- Use tax-advantaged accounts for frequent trading")
        report.append("- Gift appreciated stock to charity")

        report.append("\n*Tax rates are for 2024. Consult a tax professional for personalized advice.*")
        return "\n".join(report)

    def _explain_tax_loss_harvesting(self) -> str:
        """
        Explains tax-loss harvesting strategy.
        """
        report = ["**Tax-Loss Harvesting**\n"]

        report.append("**What is it?**")
        report.append("Selling investments at a loss to offset capital gains and reduce your tax bill.")

        report.append("\n**How it works**:")
        report.append("1. Sell investments that have declined in value")
        report.append("2. Use losses to offset capital gains")
        report.append("3. Can offset up to $3,000 of ordinary income per year")
        report.append("4. Excess losses carry forward to future years")

        report.append("\n**Wash Sale Rule (Important!)**:")
        report.append("- Cannot buy substantially identical security within 30 days")
        report.append("- Applies 30 days before AND after the sale")
        report.append("- Violating this rule disallows the loss deduction")

        report.append("\n**Example**:")
        report.append("- You have $10,000 in gains from Stock A")
        report.append("- You sell Stock B at a $4,000 loss")
        report.append("- Net taxable gain: $6,000")

        report.append("\n**Best Practices**:")
        report.append("- Harvest losses at year-end")
        report.append("- Replace sold investments with similar (not identical) funds")
        report.append("- Keep records of all transactions")

        report.append("\n*This is for educational purposes only. Consult a tax professional for personalized advice.*")
        return "\n".join(report)

    def _compare_accounts(self, account1: str, account2: str) -> str:
        """
        Compares two account types.
        """
        acc1 = self.tax_knowledge.get(account1)
        acc2 = self.tax_knowledge.get(account2)

        if not acc1 or not acc2:
            return "Unable to compare accounts."

        report = [f"**{acc1['name']} vs {acc2['name']}**\n"]

        report.append("| Feature | " + acc1['name'] + " | " + acc2['name'] + " |")
        report.append("|---------|" + "-" * len(acc1['name']) + "---|" + "-" * len(acc2['name']) + "---|")
        report.append(f"| Contribution Limit | {acc1['contribution_limit_2024']} | {acc2['contribution_limit_2024']} |")
        report.append(f"| Tax Treatment | {acc1['tax_treatment']} | {acc2['tax_treatment']} |")

        report.append("\n**When to choose " + acc1['name'] + "**:")
        report.append("- You're in a higher tax bracket now than expected in retirement")
        report.append("- You want to reduce current taxable income")

        report.append(f"\n**When to choose {acc2['name']}**:")
        report.append("- You expect to be in a higher tax bracket in retirement")
        report.append("- You want tax-free withdrawals in retirement")

        report.append("\n*Consider contributing to both if eligible!*")
        return "\n".join(report)

    def _compare_all_accounts(self) -> str:
        """
        Provides overview of all tax-advantaged accounts.
        """
        report = ["**Tax-Advantaged Account Comparison (2024)**\n"]

        report.append("| Account | Contribution Limit | Tax Treatment |")
        report.append("|---------|-------------------|---------------|")

        for key, acc in self.tax_knowledge.items():
            report.append(f"| {acc['name']} | {acc['contribution_limit_2024']} | {acc['tax_treatment']} |")

        report.append("\n**Priority Order (General Guidance)**:")
        report.append("1. 401(k) up to employer match (free money)")
        report.append("2. Max out HSA (if eligible)")
        report.append("3. Max out Roth IRA (if eligible)")
        report.append("4. Max out 401(k)")
        report.append("5. Taxable brokerage account")

        report.append("\n*Individual situations vary. This is general guidance only.*")
        return "\n".join(report)

    def _show_contribution_limits(self) -> str:
        """
        Shows 2024 contribution limits.
        """
        report = ["**2024 Contribution Limits**\n"]

        for key, acc in self.tax_knowledge.items():
            report.append(f"- **{acc['name']}**: {acc['contribution_limit_2024']}")

        report.append("\n**Catch-up Contributions** (age 50+):")
        report.append("- 401(k): Additional $7,500")
        report.append("- IRA: Additional $1,000")
        report.append("- HSA: Additional $1,000")

        return "\n".join(report)

    def _answer_tax_question(self, query: str) -> str:
        """
        Uses LLM to answer general tax questions.
        """
        # Build context from knowledge base
        context_parts = []
        for key, acc in self.tax_knowledge.items():
            context_parts.append(f"{acc['name']}: {acc['tax_treatment']}, Limit: {acc['contribution_limit_2024']}")

        context = "\n".join(context_parts)

        prompt = ChatPromptTemplate.from_messages([
            ("system", """You are a tax education assistant. Answer the user's question about
            investment-related taxes in a clear, educational manner. Use the context provided.

            Important guidelines:
            - This is for educational purposes only
            - Always recommend consulting a tax professional for personalized advice
            - Focus on general concepts, not specific tax advice
            - Use 2024 tax rules and limits

            Context:
            {context}

            Capital Gains Rates:
            - Short-term (< 1 year): Taxed as ordinary income
            - Long-term (> 1 year): 0%, 15%, or 20% based on income"""),
            ("user", "{query}")
        ])

        chain = prompt | self.llm | StrOutputParser()

        try:
            response = chain.invoke({"context": context, "query": query})
            return response + "\n\n*This is for educational purposes only. Consult a tax professional for personalized advice.*"
        except Exception as e:
            return f"Error processing tax question: {e}"
