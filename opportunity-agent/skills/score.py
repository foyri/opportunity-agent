"""
Score Skill - LLM-based match analysis with feedback loop
"""
import json
import sqlite3
from dataclasses import dataclass
from typing import List, Dict, Optional
from datetime import datetime


@dataclass
class MatchResult:
    opportunity_id: str
    score: int  # 0-100
    confidence: str  # 'high', 'medium', 'low'
    fits: List[str]
    gaps: List[str]
    angle: str
    reasoning: str
    scored_at: str = None
    
    def __post_init__(self):
        if self.scored_at is None:
            self.scored_at = datetime.now().isoformat()
    
    def to_dict(self) -> Dict:
        return {
            'score': self.score,
            'confidence': self.confidence,
            'fits': self.fits,
            'gaps': self.gaps,
            'angle': self.angle,
            'reasoning': self.reasoning,
            'scored_at': self.scored_at
        }


class OpportunityScorer:
    """Scores opportunities using LLM match analysis."""
    
    def __init__(self, config: dict = None):
        if config is None:
            with open("config.json", 'r') as f:
                config = json.load(f)
        self.config = config
        self.profile = config.get('profile', {})
        self.preferences = config.get('preferences', {})
        self._load_prompts()
        self._load_feedback_history()
    
    def _load_prompts(self):
        """Load scoring prompts from files."""
        try:
            with open('prompts/score_system.txt', 'r') as f:
                self.system_prompt = f.read()
        except FileNotFoundError:
            self.system_prompt = self._default_system_prompt()
        
        try:
            with open('prompts/score_user.txt', 'r') as f:
                self.user_prompt_template = f.read()
        except FileNotFoundError:
            self.user_prompt_template = self._default_user_prompt()
    
    def _load_feedback_history(self):
        """Load 👍/👎 feedback history for prompt tuning."""
        try:
            with open('data/feedback.json', 'r') as f:
                self.feedback = json.load(f)
        except FileNotFoundError:
            self.feedback = {'thumbs_up': [], 'thumbs_down': [], 'patterns': {}}
    
    def _default_system_prompt(self) -> str:
        """Default system prompt for scoring."""
        return """You are an expert career advisor specializing in AI Product Management and EdTech roles.
Your task is to analyze job opportunities and provide structured match scores.

Scoring Guidelines:
- 90-100: Dream role - perfect alignment with skills, interests, and career goals
- 80-89: Strong match - most requirements met, minor gaps
- 70-79: Good match - solid fit with some gaps to address
- 60-69: Potential match - interesting but significant gaps
- 0-59: Low match - not aligned with profile or goals

Confidence Levels:
- high: Clear information, confident assessment
- medium: Some ambiguity but reasonable inference
- low: Insufficient information to judge accurately

Output must be valid JSON with these fields:
{
  "score": <int 0-100>,
  "confidence": "high|medium|low",
  "fits": ["string", ...],
  "gaps": ["string", ...],
  "angle": "string - strategic positioning advice",
  "reasoning": "string - brief explanation of score"
}"""
    
    def _default_user_prompt(self) -> str:
        """Default user prompt template."""
        return """Analyze this job opportunity for the candidate.

CANDIDATE PROFILE:
Name: {name}
Background: {background}
Skills: {skills}
Experience: {experience}
Interests: {interests}
Career Goals: {goals}
Location Preference: {location_pref}
Salary Expectation: {salary_expectation}

JOB OPPORTUNITY:
Title: {title}
Company: {company}
Location: {location}
Description: {description}
Salary: {salary}
Posted: {posted_date}
Source: {source}

{feedback_context}

Provide a structured match analysis in JSON format."""
    
    def _build_profile_text(self) -> Dict[str, str]:
        """Build profile text sections from config."""
        p = self.profile
        prefs = self.preferences
        return {
            'candidate_name': p.get('name', 'Candidate'),
            'current_role': p.get('title', 'Professional'),
            'experience_summary': f"{p.get('experience_years', 0)} years experience",
            'skills': ', '.join(p.get('skills', [])),
            'desired_roles': ', '.join(prefs.get('target_roles', [])),
            'preferred_locations': ', '.join(prefs.get('locations', [])),
            'salary_expectation': prefs.get('salary_range', 'Competitive'),
            'constraints': p.get('constraints', 'None specified'),
            'background_notes': '; '.join(p.get('background', []))
        }
    
    def _get_feedback_context(self) -> str:
        """Generate feedback context from historical 👍/👎 data."""
        if not self.feedback['thumbs_up'] and not self.feedback['thumbs_down']:
            return ""
        
        context = "\nHISTORICAL FEEDBACK PATTERNS:\n"
        
        if self.feedback['thumbs_up']:
            context += "Previously rated HIGH matches had these characteristics:\n"
            for item in self.feedback['thumbs_up'][-3:]:  # Last 3 positive
                context += f"- {item.get('pattern', 'Unknown pattern')}\n"
        
        if self.feedback['thumbs_down']:
            context += "Previously rated LOW matches had these characteristics:\n"
            for item in self.feedback['thumbs_down'][-3:]:  # Last 3 negative
                context += f"- {item.get('pattern', 'Unknown pattern')}\n"
        
        return context
    
    def _op_to_dict(self, op) -> Dict:
        """Convert Opportunity object or dict to dict."""
        if hasattr(op, '__dict__'):
            return {
                'id': op.id,
                'title': op.title,
                'company': op.company,
                'location': op.location,
                'description': op.description,
                'url': getattr(op, 'url', ''),
                'salary': getattr(op, 'salary', ''),
                'posted_date': getattr(op, 'posted_date', ''),
                'source': op.source,
            }
        return op
    
    def score_opportunity(self, op) -> MatchResult:
        """Score a single opportunity using LLM."""
        op_dict = self._op_to_dict(op)
        profile = self._build_profile_text()
        feedback_ctx = self._get_feedback_context()
        
        # Build the prompt
        user_prompt = self.user_prompt_template.format(
            **profile,
            title=op_dict.get('title', ''),
            company=op_dict.get('company', ''),
            location=op_dict.get('location', ''),
            description=op_dict.get('description', '')[:3000],  # Limit length
            salary=op_dict.get('salary', 'Not specified'),
            url=op_dict.get('url', ''),
            posted_date=op_dict.get('posted_date', ''),
            source=op_dict.get('source', ''),
            feedback_context=feedback_ctx
        )
        
        # TODO: Call actual LLM API here
        # For now, return a mock result for testing
        result = self._mock_llm_call(user_prompt)
        
        return MatchResult(
            opportunity_id=op_dict.get('id'),
            score=result['score'],
            confidence=result['confidence'],
            fits=result['fits'],
            gaps=result['gaps'],
            angle=result['angle'],
            reasoning=result['reasoning']
        )
    
    def _mock_llm_call(self, prompt: str) -> Dict:
        """Mock LLM call for testing - replace with actual API call."""
        # This is a placeholder - implement actual LLM integration
        # Options: OpenAI GPT-4, Claude, local models via Ollama, etc.
        return {
            'score': 75,
            'confidence': 'medium',
            'fits': ['Relevant industry experience', 'Matching skill set'],
            'gaps': ['Specific tool experience may be lacking'],
            'angle': 'Emphasize transferable skills and learning ability',
            'reasoning': 'Good overall match with some areas to address'
        }
    
    def score_batch(self, opportunities) -> List[Dict]:
        """Score multiple opportunities and return dicts with analysis."""
        results = []
        for op in opportunities:
            try:
                match_result = self.score_opportunity(op)
                op_dict = self._op_to_dict(op)
                # Merge opportunity data with match analysis
                scored_op = {
                    **op_dict,
                    'score': match_result.score,
                    'confidence': match_result.confidence,
                    'fits': match_result.fits,
                    'gaps': match_result.gaps,
                    'angle': match_result.angle,
                }
                results.append(scored_op)
            except Exception as e:
                op_id = op.id if hasattr(op, 'id') else op.get('id', 'unknown')
                print(f"[score] Error scoring {op_id}: {e}")
        return results
    
    def save_scores(self, results: List[MatchResult], db_path: str):
        """Save scores to database."""
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        for result in results:
            try:
                cursor.execute('''
                    UPDATE opportunities 
                    SET score = ?, match_analysis = ?, status = 'scored'
                    WHERE id = ?
                ''', (
                    result.score,
                    json.dumps(result.to_dict()),
                    result.opportunity_id
                ))
            except Exception as e:
                print(f"[score] DB error for {result.opportunity_id}: {e}")
        
        conn.commit()
        conn.close()
        print(f"[score] Saved {len(results)} scores")
    
    def record_feedback(self, opportunity_id: str, rating: str, notes: str = ""):
        """Record 👍/👎 feedback for learning."""
        entry = {
            'opportunity_id': opportunity_id,
            'rating': rating,  # 'up' or 'down'
            'notes': notes,
            'timestamp': datetime.now().isoformat()
        }
        
        if rating == 'up':
            self.feedback['thumbs_up'].append(entry)
        else:
            self.feedback['thumbs_down'].append(entry)
        
        # Save feedback
        with open('data/feedback.json', 'w') as f:
            json.dump(self.feedback, f, indent=2)
        
        print(f"[score] Recorded {rating} feedback for {opportunity_id}")


if __name__ == "__main__":
    # Test scoring
    scorer = ScoreSkill()
    test_op = {
        'id': 'test_001',
        'title': 'AI Product Manager',
        'company': 'TestCorp',
        'location': 'Beijing',
        'description': 'Looking for PM with AI/ML experience...',
        'salary': '30-50k',
        'source': 'test'
    }
    result = scorer.score_opportunity(test_op)
    print(f"Score: {result.score}/100 ({result.confidence})")
    print(f"Fits: {result.fits}")
    print(f"Gaps: {result.gaps}")
