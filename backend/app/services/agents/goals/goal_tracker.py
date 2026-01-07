"""Goal Tracker - Automatic goal monitoring and execution."""

from datetime import datetime, timedelta
from typing import Any

from bson import ObjectId

from app.services.agents.goals.goal_agent import GoalAgent, GoalStatus


class GoalTracker:
    """Tracks and automatically executes goal steps."""

    def __init__(self, db):
        """Initialize with database connection."""
        self.db = db
        self.goal_agent = GoalAgent(db)

    async def get_active_goals(self, company_id: str | None = None) -> list[dict]:
        """Get all active goals that need processing.

        Args:
            company_id: Optional filter by company

        Returns:
            List of active goals
        """
        query = {
            "status": {"$in": [GoalStatus.ACTIVE.value, GoalStatus.IN_PROGRESS.value]},
        }

        if company_id:
            query["company_id"] = company_id

        goals = []
        cursor = self.db.goals.find(query)

        async for doc in cursor:
            doc["id"] = str(doc.pop("_id"))
            goals.append(doc)

        return goals

    async def process_active_goals(self, company_id: str | None = None) -> dict[str, Any]:
        """Process all active goals - execute next steps.

        This should be called periodically (e.g., by a scheduler).

        Args:
            company_id: Optional filter by company

        Returns:
            Processing results
        """
        active_goals = await self.get_active_goals(company_id)

        results = {
            "processed": 0,
            "steps_executed": 0,
            "goals_completed": 0,
            "errors": [],
        }

        for goal in active_goals:
            try:
                result = await self.goal_agent.execute_next_step(
                    goal_id=goal["id"],
                    company_id=goal["company_id"],
                )

                results["processed"] += 1

                if result.get("success"):
                    results["steps_executed"] += 1

                    if result.get("goal_completed"):
                        results["goals_completed"] += 1
                else:
                    results["errors"].append({
                        "goal_id": goal["id"],
                        "error": result.get("error"),
                    })

            except Exception as e:
                results["errors"].append({
                    "goal_id": goal["id"],
                    "error": str(e),
                })

        return results

    async def check_deadlines(self, company_id: str | None = None) -> list[dict]:
        """Check for goals approaching deadline.

        Args:
            company_id: Optional filter by company

        Returns:
            List of goals with deadline warnings
        """
        now = datetime.utcnow()
        warning_threshold = now + timedelta(days=3)

        query = {
            "status": {"$in": [GoalStatus.ACTIVE.value, GoalStatus.IN_PROGRESS.value]},
            "deadline": {"$lte": warning_threshold, "$gte": now},
        }

        if company_id:
            query["company_id"] = company_id

        warnings = []
        cursor = self.db.goals.find(query)

        async for doc in cursor:
            days_left = (doc["deadline"] - now).days

            # Calculate progress
            steps = doc.get("steps", [])
            total = len(steps)
            completed = sum(1 for s in steps if s.get("status") == "completed")
            progress = (completed / total * 100) if total > 0 else 0

            warnings.append({
                "goal_id": str(doc["_id"]),
                "company_id": doc["company_id"],
                "title": doc["title"],
                "deadline": doc["deadline"].isoformat(),
                "days_left": days_left,
                "progress_percentage": progress,
                "at_risk": progress < (100 - days_left * 20),  # Simple risk calculation
            })

        return warnings

    async def get_overdue_goals(self, company_id: str | None = None) -> list[dict]:
        """Get goals that are past their deadline.

        Args:
            company_id: Optional filter by company

        Returns:
            List of overdue goals
        """
        now = datetime.utcnow()

        query = {
            "status": {"$in": [GoalStatus.ACTIVE.value, GoalStatus.IN_PROGRESS.value]},
            "deadline": {"$lt": now},
        }

        if company_id:
            query["company_id"] = company_id

        overdue = []
        cursor = self.db.goals.find(query)

        async for doc in cursor:
            days_overdue = (now - doc["deadline"]).days

            steps = doc.get("steps", [])
            total = len(steps)
            completed = sum(1 for s in steps if s.get("status") == "completed")

            overdue.append({
                "goal_id": str(doc["_id"]),
                "company_id": doc["company_id"],
                "title": doc["title"],
                "deadline": doc["deadline"].isoformat(),
                "days_overdue": days_overdue,
                "completed_steps": completed,
                "total_steps": total,
            })

        return overdue

    async def get_goal_statistics(self, company_id: str) -> dict[str, Any]:
        """Get statistics about company goals.

        Args:
            company_id: Company ID

        Returns:
            Goal statistics
        """
        pipeline = [
            {"$match": {"company_id": company_id}},
            {"$group": {
                "_id": "$status",
                "count": {"$sum": 1},
            }},
        ]

        status_counts = {}
        async for doc in self.db.goals.aggregate(pipeline):
            status_counts[doc["_id"]] = doc["count"]

        # Get category breakdown
        category_pipeline = [
            {"$match": {"company_id": company_id}},
            {"$group": {
                "_id": "$category",
                "count": {"$sum": 1},
                "completed": {
                    "$sum": {"$cond": [{"$eq": ["$status", "completed"]}, 1, 0]}
                },
            }},
        ]

        categories = {}
        async for doc in self.db.goals.aggregate(category_pipeline):
            categories[doc["_id"]] = {
                "total": doc["count"],
                "completed": doc["completed"],
            }

        # Get average completion time
        completion_pipeline = [
            {"$match": {
                "company_id": company_id,
                "status": GoalStatus.COMPLETED.value,
            }},
            {"$project": {
                "duration": {"$subtract": ["$updated_at", "$created_at"]},
            }},
            {"$group": {
                "_id": None,
                "avg_duration_ms": {"$avg": "$duration"},
            }},
        ]

        avg_completion_days = None
        async for doc in self.db.goals.aggregate(completion_pipeline):
            if doc.get("avg_duration_ms"):
                avg_completion_days = doc["avg_duration_ms"] / (1000 * 60 * 60 * 24)

        return {
            "total_goals": sum(status_counts.values()),
            "by_status": status_counts,
            "by_category": categories,
            "average_completion_days": round(avg_completion_days, 1) if avg_completion_days else None,
            "active_count": status_counts.get(GoalStatus.ACTIVE.value, 0) +
                          status_counts.get(GoalStatus.IN_PROGRESS.value, 0),
            "success_rate": round(
                status_counts.get(GoalStatus.COMPLETED.value, 0) /
                max(sum(status_counts.values()), 1) * 100,
                1
            ),
        }

    async def recommend_next_goal(self, company_id: str) -> dict[str, Any]:
        """Recommend what goal to focus on next.

        Based on:
        - Priority
        - Deadline proximity
        - Current progress
        - Resource availability

        Args:
            company_id: Company ID

        Returns:
            Recommendation with reasoning
        """
        # Get active goals sorted by priority and deadline
        pipeline = [
            {"$match": {
                "company_id": company_id,
                "status": {"$in": [GoalStatus.ACTIVE.value, GoalStatus.IN_PROGRESS.value]},
            }},
            {"$addFields": {
                "urgency_score": {
                    "$add": [
                        {"$multiply": ["$priority", 10]},
                        {"$cond": [
                            {"$ifNull": ["$deadline", False]},
                            {"$divide": [
                                {"$subtract": [
                                    {"$toDate": "$deadline"},
                                    datetime.utcnow()
                                ]},
                                -86400000  # Negative days = higher urgency
                            ]},
                            0
                        ]},
                    ]
                }
            }},
            {"$sort": {"urgency_score": -1}},
            {"$limit": 1},
        ]

        recommended = None
        async for doc in self.db.goals.aggregate(pipeline):
            doc["id"] = str(doc.pop("_id"))
            recommended = doc

        if not recommended:
            return {
                "has_recommendation": False,
                "message": "Brak aktywnych celów do realizacji",
            }

        # Calculate progress
        steps = recommended.get("steps", [])
        total = len(steps)
        completed = sum(1 for s in steps if s.get("status") == "completed")
        pending = [s for s in steps if s.get("status") == "pending"]

        return {
            "has_recommendation": True,
            "goal": {
                "id": recommended["id"],
                "title": recommended["title"],
                "category": recommended["category"],
                "priority": recommended["priority"],
                "deadline": recommended.get("deadline"),
                "progress": f"{completed}/{total} kroków",
            },
            "reasoning": self._generate_reasoning(recommended),
            "next_step": pending[0] if pending else None,
        }

    def _generate_reasoning(self, goal: dict) -> str:
        """Generate reasoning for goal recommendation."""
        reasons = []

        if goal.get("priority", 0) >= 4:
            reasons.append(f"wysoki priorytet ({goal['priority']}/5)")

        if goal.get("deadline"):
            days_left = (goal["deadline"] - datetime.utcnow()).days
            if days_left < 0:
                reasons.append(f"przekroczony termin o {abs(days_left)} dni!")
            elif days_left <= 7:
                reasons.append(f"termin za {days_left} dni")

        steps = goal.get("steps", [])
        in_progress = sum(1 for s in steps if s.get("status") == "in_progress")
        if in_progress > 0:
            reasons.append("ma rozpoczęte kroki w toku")

        if not reasons:
            reasons.append("następny w kolejce")

        return "Rekomendowany ze względu na: " + ", ".join(reasons)
