"""Autonomous Goal Agent - Self-directing agent for achieving business goals."""

from datetime import datetime, timedelta
from enum import Enum
from typing import Any

from bson import ObjectId
from crewai import Agent, Task, Crew, Process
from langchain_openai import ChatOpenAI
from pydantic import BaseModel, Field

from app.core.config import settings
from app.services.agents.enhanced_memory import EnhancedMemoryService
from app.services.agents.tools.web_search import search_tool


class GoalStatus(str, Enum):
    """Goal status."""
    DRAFT = "draft"
    ACTIVE = "active"
    IN_PROGRESS = "in_progress"
    PAUSED = "paused"
    COMPLETED = "completed"
    FAILED = "failed"


class GoalStep(BaseModel):
    """Single step in goal execution."""
    id: str = Field(default_factory=lambda: str(ObjectId()))
    order: int
    description: str
    status: str = "pending"  # pending, in_progress, completed, failed
    agent_type: str = ""  # Which agent handles this step
    started_at: datetime | None = None
    completed_at: datetime | None = None
    result: dict = Field(default_factory=dict)
    error: str | None = None


class Goal(BaseModel):
    """Business goal to achieve autonomously."""
    id: str = Field(default_factory=lambda: str(ObjectId()))
    company_id: str
    title: str
    description: str
    category: str  # marketing, sales, finance, hr, support
    target_metric: str = ""
    target_value: float | None = None
    current_value: float | None = None
    deadline: datetime | None = None
    status: GoalStatus = GoalStatus.DRAFT
    priority: int = 1  # 1-5, 5 is highest
    steps: list[GoalStep] = Field(default_factory=list)
    research_data: dict = Field(default_factory=dict)
    strategy: dict = Field(default_factory=dict)
    progress_reports: list[dict] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


def _get_llm():
    """Get LLM instance."""
    return ChatOpenAI(
        model="gpt-4o-mini",
        temperature=0.4,
        api_key=settings.OPENAI_API_KEY,
    )


class GoalAgent:
    """Autonomous agent for achieving business goals."""

    def __init__(self, db):
        """Initialize with database connection."""
        self.db = db
        self.enhanced_memory = EnhancedMemoryService(db)
        self.llm = _get_llm()

    async def create_goal(
        self,
        company_id: str,
        title: str,
        description: str,
        category: str,
        target_metric: str = "",
        target_value: float | None = None,
        deadline: datetime | None = None,
        priority: int = 1,
    ) -> Goal:
        """Create a new goal and generate execution plan.

        Args:
            company_id: Company ID
            title: Goal title
            description: Detailed description
            category: Goal category (marketing, sales, etc.)
            target_metric: What to measure
            target_value: Target value to achieve
            deadline: Target deadline
            priority: Priority level (1-5)

        Returns:
            Created Goal with execution plan
        """
        goal = Goal(
            company_id=company_id,
            title=title,
            description=description,
            category=category,
            target_metric=target_metric,
            target_value=target_value,
            deadline=deadline,
            priority=priority,
        )

        # Research and create strategy
        goal = await self._research_goal(goal)
        goal = await self._create_strategy(goal)
        goal = await self._generate_steps(goal)

        # Save to database
        goal_dict = goal.model_dump()
        goal_dict["_id"] = ObjectId(goal.id)
        await self.db.goals.insert_one(goal_dict)

        return goal

    async def _research_goal(self, goal: Goal) -> Goal:
        """Research best practices and competition for goal."""
        tools = [search_tool] if settings.TAVILY_API_KEY else []

        researcher = Agent(
            role="Business Research Analyst",
            goal="Zbadać najlepsze praktyki i strategie dla osiągnięcia celu biznesowego",
            backstory="""Jesteś doświadczonym analitykiem biznesowym.
            Specjalizujesz się w badaniu rynku, trendów i konkurencji.
            Potrafisz znaleźć sprawdzone strategie i praktyki.""",
            tools=tools,
            llm=self.llm,
            verbose=False,
        )

        research_task = Task(
            description=f"""
            Przeprowadź badanie dla celu biznesowego:

            CEL: {goal.title}
            OPIS: {goal.description}
            KATEGORIA: {goal.category}
            METRYKA: {goal.target_metric} -> {goal.target_value}
            DEADLINE: {goal.deadline}

            Zbadaj:
            1. Najlepsze praktyki w tej dziedzinie
            2. Sprawdzone strategie
            3. Typowe błędy do uniknięcia
            4. Benchmarki branżowe
            5. Narzędzia i techniki

            Zwróć w formacie JSON:
            {{
                "best_practices": ["praktyka 1", "praktyka 2"],
                "proven_strategies": ["strategia 1", "strategia 2"],
                "common_mistakes": ["błąd 1", "błąd 2"],
                "benchmarks": {{"metric": "value"}},
                "tools_techniques": ["narzędzie 1", "technika 1"],
                "key_insights": ["insight 1", "insight 2"]
            }}
            """,
            agent=researcher,
            expected_output="Research results in JSON format",
        )

        crew = Crew(
            agents=[researcher],
            tasks=[research_task],
            process=Process.sequential,
            verbose=False,
        )

        result = crew.kickoff()

        # Parse research
        import json
        import re

        result_text = str(result)
        json_match = re.search(r'\{[\s\S]*\}', result_text)

        if json_match:
            try:
                goal.research_data = json.loads(json_match.group())
            except json.JSONDecodeError:
                goal.research_data = {"raw_research": result_text}
        else:
            goal.research_data = {"raw_research": result_text}

        return goal

    async def _create_strategy(self, goal: Goal) -> Goal:
        """Create execution strategy based on research."""
        # Get company context
        context = await self.enhanced_memory.get_comprehensive_context(
            company_id=goal.company_id,
            query=f"{goal.title}: {goal.description}",
            include_web=False,
        )

        strategist = Agent(
            role="Business Strategist",
            goal="Stworzyć skuteczną strategię realizacji celu",
            backstory="""Jesteś doświadczonym strategiem biznesowym.
            Tworzysz realistyczne, mierzalne plany działania.
            Uwzględniasz specyfikę firmy i jej zasoby.""",
            tools=[],
            llm=self.llm,
            verbose=False,
        )

        strategy_task = Task(
            description=f"""
            Stwórz strategię realizacji celu:

            CEL: {goal.title}
            OPIS: {goal.description}
            METRYKA: {goal.target_metric} -> {goal.target_value}
            DEADLINE: {goal.deadline}

            WYNIKI BADAŃ:
            {goal.research_data}

            KONTEKST FIRMY:
            {context.formatted_context}

            Stwórz strategię w formacie JSON:
            {{
                "approach": "Główne podejście",
                "phases": [
                    {{
                        "name": "Faza 1",
                        "duration_days": 7,
                        "objectives": ["cel 1", "cel 2"],
                        "tactics": ["taktyka 1", "taktyka 2"]
                    }}
                ],
                "kpis": [
                    {{"name": "KPI 1", "target": "wartość", "frequency": "dzienna"}}
                ],
                "resources_needed": ["zasób 1", "zasób 2"],
                "risks": [
                    {{"risk": "opis", "mitigation": "jak zminimalizować"}}
                ],
                "success_criteria": ["kryterium 1", "kryterium 2"]
            }}
            """,
            agent=strategist,
            expected_output="Strategy in JSON format",
        )

        crew = Crew(
            agents=[strategist],
            tasks=[strategy_task],
            process=Process.sequential,
            verbose=False,
        )

        result = crew.kickoff()

        import json
        import re

        result_text = str(result)
        json_match = re.search(r'\{[\s\S]*\}', result_text)

        if json_match:
            try:
                goal.strategy = json.loads(json_match.group())
            except json.JSONDecodeError:
                goal.strategy = {"raw_strategy": result_text}
        else:
            goal.strategy = {"raw_strategy": result_text}

        return goal

    async def _generate_steps(self, goal: Goal) -> Goal:
        """Generate concrete execution steps from strategy."""
        planner = Agent(
            role="Action Planner",
            goal="Przekształcić strategię w konkretne kroki do wykonania",
            backstory="""Jesteś ekspertem od planowania projektów.
            Tworzysz szczegółowe, wykonalne kroki z przypisanymi odpowiedzialnościami.""",
            tools=[],
            llm=self.llm,
            verbose=False,
        )

        agent_types = {
            "marketing": ["instagram", "copywriter", "content_calendar"],
            "sales": ["proposal", "lead_scorer", "crm"],
            "finance": ["invoice", "cashflow", "report"],
            "hr": ["recruiter", "interviewer", "onboarding"],
            "support": ["ticket", "faq", "sentiment"],
        }

        available_agents = agent_types.get(goal.category, ["general"])

        planning_task = Task(
            description=f"""
            Stwórz listę kroków do realizacji celu:

            CEL: {goal.title}
            STRATEGIA: {goal.strategy}

            DOSTĘPNI AGENCI DLA KATEGORII {goal.category}:
            {available_agents}

            Stwórz kroki w formacie JSON (lista):
            [
                {{
                    "order": 1,
                    "description": "Dokładny opis kroku",
                    "agent_type": "typ agenta z listy",
                    "estimated_duration": "np. 1 dzień",
                    "dependencies": [numery kroków od których zależy]
                }}
            ]

            Maksymalnie 10 kroków. Każdy krok musi być konkretny i wykonalny.
            """,
            agent=planner,
            expected_output="List of steps in JSON format",
        )

        crew = Crew(
            agents=[planner],
            tasks=[planning_task],
            process=Process.sequential,
            verbose=False,
        )

        result = crew.kickoff()

        import json
        import re

        result_text = str(result)
        json_match = re.search(r'\[[\s\S]*\]', result_text)

        steps = []
        if json_match:
            try:
                steps_data = json.loads(json_match.group())
                for step_data in steps_data:
                    steps.append(GoalStep(
                        order=step_data.get("order", len(steps) + 1),
                        description=step_data.get("description", ""),
                        agent_type=step_data.get("agent_type", "general"),
                    ))
            except json.JSONDecodeError:
                pass

        goal.steps = steps
        return goal

    async def start_goal(self, goal_id: str, company_id: str) -> Goal | None:
        """Start executing a goal."""
        goal_doc = await self.db.goals.find_one({
            "_id": ObjectId(goal_id),
            "company_id": company_id,
        })

        if not goal_doc:
            return None

        await self.db.goals.update_one(
            {"_id": ObjectId(goal_id)},
            {
                "$set": {
                    "status": GoalStatus.ACTIVE.value,
                    "updated_at": datetime.utcnow(),
                }
            }
        )

        goal_doc["status"] = GoalStatus.ACTIVE.value
        goal_doc["id"] = str(goal_doc.pop("_id"))
        return Goal(**goal_doc)

    async def pause_goal(self, goal_id: str, company_id: str) -> Goal | None:
        """Pause a running goal."""
        result = await self.db.goals.update_one(
            {"_id": ObjectId(goal_id), "company_id": company_id},
            {
                "$set": {
                    "status": GoalStatus.PAUSED.value,
                    "updated_at": datetime.utcnow(),
                }
            }
        )

        if result.modified_count == 0:
            return None

        goal_doc = await self.db.goals.find_one({"_id": ObjectId(goal_id)})
        goal_doc["id"] = str(goal_doc.pop("_id"))
        return Goal(**goal_doc)

    async def execute_next_step(self, goal_id: str, company_id: str) -> dict[str, Any]:
        """Execute the next pending step in a goal.

        Returns:
            Result of step execution
        """
        goal_doc = await self.db.goals.find_one({
            "_id": ObjectId(goal_id),
            "company_id": company_id,
            "status": {"$in": [GoalStatus.ACTIVE.value, GoalStatus.IN_PROGRESS.value]},
        })

        if not goal_doc:
            return {"success": False, "error": "Goal not found or not active"}

        goal_doc["id"] = str(goal_doc.pop("_id"))
        goal = Goal(**goal_doc)

        # Find next pending step
        next_step = None
        step_index = -1
        for i, step in enumerate(goal.steps):
            if step.status == "pending":
                next_step = step
                step_index = i
                break

        if not next_step:
            # All steps completed
            await self._complete_goal(goal_id)
            return {"success": True, "message": "All steps completed", "goal_completed": True}

        # Update goal status to in_progress
        await self.db.goals.update_one(
            {"_id": ObjectId(goal_id)},
            {"$set": {"status": GoalStatus.IN_PROGRESS.value}}
        )

        # Mark step as in_progress
        goal.steps[step_index].status = "in_progress"
        goal.steps[step_index].started_at = datetime.utcnow()

        await self._save_steps(goal_id, goal.steps)

        # Execute the step
        result = await self._execute_step(goal, next_step)

        # Update step with result
        goal.steps[step_index].completed_at = datetime.utcnow()
        if result["success"]:
            goal.steps[step_index].status = "completed"
            goal.steps[step_index].result = result.get("result", {})
        else:
            goal.steps[step_index].status = "failed"
            goal.steps[step_index].error = result.get("error", "Unknown error")

        await self._save_steps(goal_id, goal.steps)

        return {
            "success": result["success"],
            "step": next_step.model_dump(),
            "result": result,
        }

    async def _execute_step(self, goal: Goal, step: GoalStep) -> dict[str, Any]:
        """Execute a single step."""
        # Get context for the step
        context = await self.enhanced_memory.get_comprehensive_context(
            company_id=goal.company_id,
            query=f"{goal.title}: {step.description}",
            agent=step.agent_type,
        )

        executor = Agent(
            role=f"{step.agent_type.title()} Specialist",
            goal=f"Wykonać krok: {step.description}",
            backstory=f"""Jesteś specjalistą w dziedzinie {goal.category}.
            Wykonujesz zadania w ramach większego celu biznesowego.
            Działasz precyzyjnie i raportjesz wyniki.""",
            tools=[search_tool] if settings.TAVILY_API_KEY else [],
            llm=self.llm,
            verbose=False,
        )

        execution_task = Task(
            description=f"""
            Wykonaj następujący krok w ramach celu biznesowego:

            CEL GŁÓWNY: {goal.title}
            STRATEGIA: {goal.strategy.get('approach', '')}

            KROK DO WYKONANIA:
            {step.description}

            KONTEKST:
            {context.formatted_context}

            Wykonaj krok i zwróć wynik w formacie JSON:
            {{
                "completed": true,
                "actions_taken": ["akcja 1", "akcja 2"],
                "outputs": {{"typ": "wynik"}},
                "recommendations": ["rekomendacja dla następnych kroków"],
                "metrics": {{"metryka": "wartość"}}
            }}
            """,
            agent=executor,
            expected_output="Step execution result in JSON format",
        )

        crew = Crew(
            agents=[executor],
            tasks=[execution_task],
            process=Process.sequential,
            verbose=False,
        )

        try:
            result = crew.kickoff()

            import json
            import re

            result_text = str(result)
            json_match = re.search(r'\{[\s\S]*\}', result_text)

            if json_match:
                try:
                    result_data = json.loads(json_match.group())
                    return {"success": True, "result": result_data}
                except json.JSONDecodeError:
                    return {"success": True, "result": {"raw_output": result_text}}
            else:
                return {"success": True, "result": {"raw_output": result_text}}

        except Exception as e:
            return {"success": False, "error": str(e)}

    async def _save_steps(self, goal_id: str, steps: list[GoalStep]) -> None:
        """Save updated steps to database."""
        steps_data = [s.model_dump() for s in steps]
        await self.db.goals.update_one(
            {"_id": ObjectId(goal_id)},
            {
                "$set": {
                    "steps": steps_data,
                    "updated_at": datetime.utcnow(),
                }
            }
        )

    async def _complete_goal(self, goal_id: str) -> None:
        """Mark goal as completed."""
        await self.db.goals.update_one(
            {"_id": ObjectId(goal_id)},
            {
                "$set": {
                    "status": GoalStatus.COMPLETED.value,
                    "updated_at": datetime.utcnow(),
                }
            }
        )

    async def get_progress_report(self, goal_id: str, company_id: str) -> dict[str, Any]:
        """Generate a progress report for a goal."""
        goal_doc = await self.db.goals.find_one({
            "_id": ObjectId(goal_id),
            "company_id": company_id,
        })

        if not goal_doc:
            return {"success": False, "error": "Goal not found"}

        goal_doc["id"] = str(goal_doc.pop("_id"))
        goal = Goal(**goal_doc)

        # Calculate progress
        total_steps = len(goal.steps)
        completed_steps = sum(1 for s in goal.steps if s.status == "completed")
        failed_steps = sum(1 for s in goal.steps if s.status == "failed")

        progress_percentage = (completed_steps / total_steps * 100) if total_steps > 0 else 0

        # Generate report with LLM
        reporter = Agent(
            role="Progress Reporter",
            goal="Wygenerować zwięzły raport postępu",
            backstory="Tworzysz jasne, merytoryczne raporty postępu projektów.",
            tools=[],
            llm=self.llm,
            verbose=False,
        )

        report_task = Task(
            description=f"""
            Wygeneruj raport postępu dla celu:

            CEL: {goal.title}
            STATUS: {goal.status.value}
            POSTĘP: {completed_steps}/{total_steps} kroków ({progress_percentage:.1f}%)
            NIEPOWODZENIA: {failed_steps}

            UKOŃCZONE KROKI:
            {[s.model_dump() for s in goal.steps if s.status == "completed"]}

            STRATEGIA:
            {goal.strategy}

            Stwórz raport w formacie JSON:
            {{
                "summary": "Krótkie podsumowanie (2-3 zdania)",
                "progress_percentage": {progress_percentage},
                "achievements": ["osiągnięcie 1", "osiągnięcie 2"],
                "challenges": ["wyzwanie 1"],
                "next_actions": ["następna akcja"],
                "estimated_completion": "szacowany czas ukończenia",
                "risk_level": "low/medium/high"
            }}
            """,
            agent=reporter,
            expected_output="Progress report in JSON format",
        )

        crew = Crew(
            agents=[reporter],
            tasks=[report_task],
            process=Process.sequential,
            verbose=False,
        )

        result = crew.kickoff()

        import json
        import re

        result_text = str(result)
        json_match = re.search(r'\{[\s\S]*\}', result_text)

        report = {
            "goal_id": goal.id,
            "title": goal.title,
            "status": goal.status.value,
            "progress_percentage": progress_percentage,
            "completed_steps": completed_steps,
            "total_steps": total_steps,
            "failed_steps": failed_steps,
            "generated_at": datetime.utcnow().isoformat(),
        }

        if json_match:
            try:
                report_data = json.loads(json_match.group())
                report.update(report_data)
            except json.JSONDecodeError:
                pass

        # Save report
        goal.progress_reports.append(report)
        await self.db.goals.update_one(
            {"_id": ObjectId(goal_id)},
            {
                "$push": {"progress_reports": report},
                "$set": {"updated_at": datetime.utcnow()},
            }
        )

        return {"success": True, "report": report}

    async def get_goals(
        self,
        company_id: str,
        status: GoalStatus | None = None,
        category: str | None = None,
        limit: int = 20,
    ) -> list[Goal]:
        """Get goals for a company."""
        query: dict = {"company_id": company_id}

        if status:
            query["status"] = status.value
        if category:
            query["category"] = category

        goals = []
        cursor = self.db.goals.find(query).sort("created_at", -1).limit(limit)

        async for doc in cursor:
            doc["id"] = str(doc.pop("_id"))
            goals.append(Goal(**doc))

        return goals

    async def get_goal(self, goal_id: str, company_id: str) -> Goal | None:
        """Get a specific goal."""
        goal_doc = await self.db.goals.find_one({
            "_id": ObjectId(goal_id),
            "company_id": company_id,
        })

        if not goal_doc:
            return None

        goal_doc["id"] = str(goal_doc.pop("_id"))
        return Goal(**goal_doc)
