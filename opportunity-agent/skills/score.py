"""
Score Skill - LLM-based match analysis with feedback loop

This module provides intelligent job opportunity scoring by:
1. Reading un-scored opportunities from SQLite database
2. Analyzing match using LLM (subagent-based analysis)
3. Generating structured scores (0-100), fits, gaps, and application angles
4. Updating database with analysis results
5. Supporting feedback loop (👍/👎) to improve future scoring
"""

import json
import sqlite3
import os
import sys
from dataclasses import dataclass, asdict
from typing import List, Dict, Optional, Any
from datetime import datetime
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))


@dataclass
class MatchResult:
    """Structured result from LLM match analysis."""
    opportunity_id: str
    score: int  # 0-100
    confidence: str  # 'high', 'medium', 'low'
    fits: List[str]
    gaps: List[str]
    angle: str
    reasoning: str
    status: str = "scored"
    scored_at: str = None
    
    def __post_init__(self):
        if self.scored_at is None:
            self.scored_at = datetime.now().isoformat()
        # Validate score range
        self.score = max(0, min(100, self.score))
    
    def to_dict(self) -> Dict:
        """Convert to dictionary for JSON serialization."""
        return {
            'opportunity_id': self.opportunity_id,
            'score': self.score,
            'confidence': self.confidence,
            'fits': self.fits,
            'gaps': self.gaps,
            'angle': self.angle,
            'reasoning': self.reasoning,
            'status': self.status,
            'scored_at': self.scored_at
        }
    
    @classmethod
    def from_llm_response(cls, opportunity_id: str, response: Dict) -> 'MatchResult':
        """Create MatchResult from LLM JSON response."""
        return cls(
            opportunity_id=opportunity_id,
            score=response.get('score', 50),
            confidence=response.get('confidence', 'medium'),
            fits=response.get('fits', []),
            gaps=response.get('gaps', []),
            angle=response.get('angle', ''),
            reasoning=response.get('reasoning', '')
        )


class OpportunityScorer:
    """Scores opportunities using LLM match analysis with feedback learning."""
    
    def __init__(self, config: dict = None, db_path: str = None, feedback_path: str = None):
        """Initialize the scorer with configuration.
        
        Args:
            config: Configuration dictionary with profile and preferences
            db_path: Path to SQLite database (default: data/opportunities.db)
            feedback_path: Path to feedback JSON file (default: data/feedback.json)
        """
        if config is None:
            config_path = Path(__file__).parent.parent / "config.json"
            with open(config_path, 'r', encoding='utf-8') as f:
                config = json.load(f)
        
        self.config = config
        self.profile = config.get('profile', {})
        self.preferences = config.get('preferences', {})
        
        # Set paths
        base_dir = Path(__file__).parent.parent
        self.db_path = db_path or str(base_dir / config.get('database', {}).get('path', 'data/opportunities.db'))
        self.feedback_path = feedback_path or str(base_dir / config.get('feedback', {}).get('path', 'data/feedback.json'))
        
        # Ensure data directory exists
        Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)
        Path(self.feedback_path).parent.mkdir(parents=True, exist_ok=True)
        
        # Load prompts and feedback history
        self._load_prompts()
        self._load_feedback_history()
    
    def _load_prompts(self):
        """Load scoring prompts from files or use defaults."""
        prompts_dir = Path(__file__).parent.parent / "prompts"
        
        # Try to load custom prompts
        system_prompt_path = prompts_dir / "score_system.txt"
        user_prompt_path = prompts_dir / "score_user.txt"
        
        if system_prompt_path.exists():
            with open(system_prompt_path, 'r', encoding='utf-8') as f:
                self.system_prompt = f.read()
        else:
            self.system_prompt = self._default_system_prompt()
        
        if user_prompt_path.exists():
            with open(user_prompt_path, 'r', encoding='utf-8') as f:
                self.user_prompt_template = f.read()
        else:
            self.user_prompt_template = self._default_user_prompt()
    
    def _load_feedback_history(self):
        """Load 👍/👎 feedback history for prompt tuning."""
        if os.path.exists(self.feedback_path):
            try:
                with open(self.feedback_path, 'r', encoding='utf-8') as f:
                    self.feedback = json.load(f)
            except (json.JSONDecodeError, IOError):
                self.feedback = {'thumbs_up': [], 'thumbs_down': [], 'patterns': {}}
        else:
            self.feedback = {'thumbs_up': [], 'thumbs_down': [], 'patterns': {}}
    
    def _default_system_prompt(self) -> str:
        """Default system prompt for LLM scoring."""
        return """You are an expert career advisor specializing in AI Product Management and EdTech roles.
Your task is to analyze job opportunities and provide structured match scores.

SCORING GUIDELINES (0-100):
- 90-100: Dream role - perfect alignment with skills, interests, and career goals
- 80-89: Strong match - most requirements met, minor gaps
- 70-79: Good match - solid fit with some gaps to address
- 60-69: Potential match - interesting but significant gaps
- 0-59: Low match - not aligned with profile or goals

CONFIDENCE LEVELS:
- high: Clear information, confident assessment
- medium: Some ambiguity but reasonable inference
- low: Insufficient information to judge accurately

OUTPUT FORMAT:
Return ONLY valid JSON with these exact fields:
{
  "score": <integer 0-100>,
  "confidence": "high|medium|low",
  "fits": ["string - specific reason this matches", ...],
  "gaps": ["string - specific requirement not met", ...],
  "angle": "string - strategic advice on how to position for this role",
  "reasoning": "string - brief explanation of the score"
}

IMPORTANT:
- Be objective and evidence-based
- Consider both explicit requirements and implicit fit
- Account for candidate's unique hybrid background (AI + Education)
- Factor in location preferences and experience level
- Return ONLY the JSON object, no markdown formatting"""

    def _default_user_prompt(self) -> str:
        """Default user prompt template for scoring."""
        return """Analyze this job opportunity for the candidate.

CANDIDATE PROFILE:
Name: {candidate_name}
Title: {current_role}
Location: {candidate_location}
Experience: {experience_summary}
Background: {background_notes}
Skills: {skills}
Target Roles: {desired_roles}
Preferred Locations: {preferred_locations}
Constraints: {constraints}

JOB OPPORTUNITY:
Title: {title}
Company: {company}
Location: {location}
Salary: {salary}
Posted: {posted_date}
Source: {source}
URL: {url}
Description:
{description}

{feedback_context}

Provide a structured match analysis in the required JSON format.
Focus on:
1. How well the role aligns with AI+Education hybrid background
2. Whether Vibe Coding / rapid prototyping skills are relevant
3. Content creation and photography skills as differentiators
4. Geographic fit and remote work possibilities"""

    def _build_profile_context(self) -> Dict[str, str]:
        """Build profile context for prompt from config."""
        p = self.profile
        prefs = self.preferences
        
        return {
            'candidate_name': p.get('name', 'Candidate'),
            'current_role': p.get('title', 'Professional'),
            'candidate_location': p.get('location', 'Not specified'),
            'experience_summary': f"{p.get('experience_years', 0)} years",
            'background_notes': '; '.join(p.get('background', [])),
            'skills': ', '.join(p.get('skills', [])),
            'desired_roles': ', '.join(prefs.get('target_roles', [])),
            'preferred_locations': ', '.join(prefs.get('locations', [])),
            'constraints': p.get('constraints', 'None specified'),
        }
    
    def _get_feedback_context(self) -> str:
        """Generate feedback context from historical 👍/👎 data."""
        if not self.feedback.get('thumbs_up') and not self.feedback.get('thumbs_down'):
            return ""
        
        context_parts = ["\nHISTORICAL FEEDBACK PATTERNS:"]
        
        if self.feedback.get('thumbs_up'):
            context_parts.append("Previously rated HIGH matches had these characteristics:")
            for item in self.feedback['thumbs_up'][-3:]:  # Last 3 positive
                pattern = item.get('pattern', item.get('notes', 'Unknown pattern'))
                context_parts.append(f"- {pattern}")
        
        if self.feedback.get('thumbs_down'):
            context_parts.append("Previously rated LOW matches had these characteristics:")
            for item in self.feedback['thumbs_down'][-3:]:  # Last 3 negative
                pattern = item.get('pattern', item.get('notes', 'Unknown pattern'))
                context_parts.append(f"- {pattern}")
        
        return '\n'.join(context_parts)
    
    def _opportunity_to_dict(self, op: Any) -> Dict:
        """Convert Opportunity object or database row to dictionary."""
        if hasattr(op, '__dict__'):
            # It's an Opportunity dataclass object
            return {
                'id': op.id,
                'title': op.title,
                'company': op.company,
                'location': op.location,
                'description': op.description,
                'url': getattr(op, 'url', ''),
                'salary': getattr(op, 'salary', 'Not specified'),
                'posted_date': getattr(op, 'posted_date', ''),
                'source': op.source,
            }
        elif isinstance(op, dict):
            return op
        elif isinstance(op, tuple):
            # Database row tuple - map to dict based on schema
            columns = ['id', 'source', 'platform', 'title', 'company', 'location', 
                      'description', 'url', 'salary_min', 'salary_max', 'posted_date',
                      'fetched_at', 'score', 'confidence', 'fits', 'gaps', 'angle', 
                      'status', 'feedback']
            return dict(zip(columns, op))
        else:
            raise ValueError(f"Unknown opportunity type: {type(op)}")
    
    def _call_llm_for_scoring(self, prompt: str) -> Dict:
        """Call LLM API for scoring. Returns parsed JSON response.
        
        In production, this would call OpenAI, Claude, or local LLM.
        For now, uses rule-based mock scoring that simulates intelligent analysis.
        """
        # TODO: Replace with actual LLM API call
        # Options: OpenAI GPT-4, Anthropic Claude, local models via Ollama
        
        # For development/testing, return mock result
        # This should be replaced with actual LLM integration
        return self._mock_llm_call(prompt)
    
    def _mock_llm_call(self, prompt: str) -> Dict:
        """Mock LLM call for testing - simulates intelligent scoring.
        
        In production, replace this with actual LLM API integration.
        """
        # Extract job info from prompt for rule-based scoring
        prompt_lower = prompt.lower()
        
        # Base score
        score = 50
        fits = []
        gaps = []
        
        # Check for AI-related keywords
        ai_keywords = ['ai', 'artificial intelligence', 'machine learning', 'ml', 'llm', '大模型']
        if any(kw in prompt_lower for kw in ai_keywords):
            score += 15
            fits.append("AI-focused role matches your AI Product Management background")
        
        # Check for education keywords
        edu_keywords = ['education', 'edtech', 'learning', 'teaching', '教育', '学习']
        if any(kw in prompt_lower for kw in edu_keywords):
            score += 20
            fits.append("Education focus aligns with your AI Education specialization")
        
        # Check for product management
        pm_keywords = ['product manager', '产品经理', 'product owner']
        if any(kw in prompt_lower for kw in pm_keywords):
            score += 10
            fits.append("Product Management role matches your core skillset")
        
        # Check for experience requirements
        exp_3plus = ['3年', '3+ years', '5年', '5+ years', 'senior', '高级']
        if any(kw in prompt_lower for kw in exp_3plus):
            score -= 10
            gaps.append("Requires more experience than you currently have (1 year)")
        
        # Check for location fit
        preferred_locs = ['remote', 'beijing', 'shanghai', 'shenzhen', 'hangzhou', '北京', '上海', '深圳', '杭州']
        if any(loc in prompt_lower for loc in preferred_locs):
            score += 5
            fits.append("Location matches your preferences")
        
        # Check for vibe coding / rapid prototyping mentions
        vibe_keywords = ['vibe coding', 'rapid prototyping', '快速原型', '创业']
        if any(kw in prompt_lower for kw in vibe_keywords):
            score += 10
            fits.append("Vibe Coding culture matches your working style")
        
        # Ensure score is within bounds
        score = max(0, min(100, score))
        
        # Determine confidence
        if len(fits) >= 3 and len(gaps) <= 1:
            confidence = "high"
        elif len(fits) >= 2:
            confidence = "medium"
        else:
            confidence = "low"
        
        # Generate angle
        if score >= 80:
            angle = "Emphasize your unique AI+Education hybrid background and Vibe Coding capabilities"
        elif score >= 60:
            angle = "Highlight transferable skills and rapid learning ability; address experience gap proactively"
        else:
            angle = "Consider if this role truly fits your career trajectory before investing time"
        
        # Default fits/gaps if empty
        if not fits:
            fits = ["Some general alignment with your profile"]
        if not gaps:
            gaps = ["Specific requirements need verification"]
        
        return {
            'score': score,
            'confidence': confidence,
            'fits': fits,
            'gaps': gaps,
            'angle': angle,
            'reasoning': f"Score based on keyword analysis: AI relevance, education focus, PM fit, experience match, location preference"
        }
    
    def score_opportunity(self, opportunity: Any) -> MatchResult:
        """Score a single opportunity using LLM analysis.
        
        Args:
            opportunity: Opportunity object, dict, or database row
            
        Returns:
            MatchResult with score, fits, gaps, and application angle
        """
        op_dict = self._opportunity_to_dict(opportunity)
        profile = self._build_profile_context()
        feedback_ctx = self._get_feedback_context()
        
        # Build the prompt
        user_prompt = self.user_prompt_template.format(
            **profile,
            job_title=op_dict.get('title', ''),
            company=op_dict.get('company', ''),
            job_location=op_dict.get('location', ''),
            description=op_dict.get('description', '')[:3000],  # Limit length
            salary=op_dict.get('salary', 'Not specified'),
            url=op_dict.get('url', ''),
            posted_date=op_dict.get('posted_date', ''),
            source=op_dict.get('source', ''),
            feedback_context=feedback_ctx
        )
        
        # Call LLM for analysis
        llm_response = self._call_llm_for_scoring(user_prompt)
        
        # Create result
        result = MatchResult.from_llm_response(
            opportunity_id=op_dict.get('id'),
            response=llm_response
        )
        
        return result
    
    def score_batch(self, opportunities: List[Any]) -> List[Dict]:
        """Score multiple opportunities and return enriched dictionaries.
        
        Args:
            opportunities: List of Opportunity objects, dicts, or database rows
            
        Returns:
            List of opportunity dictionaries with added score fields
        """
        results = []
        for op in opportunities:
            try:
                match_result = self.score_opportunity(op)
                op_dict = self._opportunity_to_dict(op)
                
                # Merge opportunity data with match analysis
                scored_op = {
                    **op_dict,
                    'score': match_result.score,
                    'confidence': match_result.confidence,
                    'fits': match_result.fits,
                    'gaps': match_result.gaps,
                    'angle': match_result.angle,
                    'reasoning': match_result.reasoning,
                    'status': 'scored'
                }
                results.append(scored_op)
                
                print(f"[score] Scored '{op_dict.get('title', 'Unknown')}' @ {op_dict.get('company', 'Unknown')}: {match_result.score}/100 ({match_result.confidence})")
                
            except Exception as e:
                op_id = op.get('id', 'unknown') if isinstance(op, dict) else getattr(op, 'id', 'unknown')
                print(f"[score] Error scoring {op_id}: {e}")
                # Still include the opportunity but with error status
                op_dict = self._opportunity_to_dict(op)
                op_dict.update({
                    'score': None,
                    'confidence': 'error',
                    'fits': [],
                    'gaps': [f"Scoring error: {str(e)}"],
                    'angle': 'Could not analyze - please review manually',
                    'status': 'error'
                })
                results.append(op_dict)
        
        return results
    
    def get_unscored_opportunities(self, limit: int = None) -> List[Dict]:
        """Fetch opportunities with status='new' from database.
        
        Args:
            limit: Maximum number of opportunities to fetch
            
        Returns:
            List of opportunity dictionaries
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        query = """
            SELECT id, source, platform, title, company, location, 
                   description, url, salary_min, salary_max, posted_date,
                   fetched_at, score, confidence, fits, gaps, angle, 
                   status, feedback
            FROM opportunities 
            WHERE status = 'new' OR score IS NULL
            ORDER BY fetched_at DESC
        """
        
        if limit:
            query += f" LIMIT {limit}"
        
        cursor.execute(query)
        rows = cursor.fetchall()
        conn.close()
        
        # Convert rows to dictionaries
        columns = ['id', 'source', 'platform', 'title', 'company', 'location', 
                  'description', 'url', 'salary_min', 'salary_max', 'posted_date',
                  'fetched_at', 'score', 'confidence', 'fits', 'gaps', 'angle', 
                  'status', 'feedback']
        
        opportunities = []
        for row in rows:
            op_dict = dict(zip(columns, row))
            # Parse JSON fields
            for field in ['fits', 'gaps']:
                if op_dict.get(field) and isinstance(op_dict[field], str):
                    try:
                        op_dict[field] = json.loads(op_dict[field])
                    except json.JSONDecodeError:
                        op_dict[field] = []
            opportunities.append(op_dict)
        
        return opportunities
    
    def save_scores(self, results: List[MatchResult]):
        """Save scores to database.
        
        Args:
            results: List of MatchResult objects to save
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        saved_count = 0
        for result in results:
            try:
                cursor.execute('''
                    UPDATE opportunities 
                    SET score = ?, 
                        confidence = ?,
                        fits = ?, 
                        gaps = ?, 
                        angle = ?,
                        status = 'scored'
                    WHERE id = ?
                ''', (
                    result.score,
                    result.confidence,
                    json.dumps(result.fits, ensure_ascii=False),
                    json.dumps(result.gaps, ensure_ascii=False),
                    result.angle,
                    result.opportunity_id
                ))
                if cursor.rowcount > 0:
                    saved_count += 1
            except Exception as e:
                print(f"[score] DB error saving score for {result.opportunity_id}: {e}")
        
        conn.commit()
        conn.close()
        print(f"[score] Saved {saved_count}/{len(results)} scores to database")
        return saved_count
    
    def save_scored_opportunities(self, opportunities: List[Dict]):
        """Save scored opportunity dictionaries to database.
        
        Args:
            opportunities: List of opportunity dictionaries with score fields
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        saved_count = 0
        for opp in opportunities:
            try:
                cursor.execute('''
                    UPDATE opportunities 
                    SET score = ?, 
                        confidence = ?,
                        fits = ?, 
                        gaps = ?, 
                        angle = ?,
                        status = ?
                    WHERE id = ?
                ''', (
                    opp.get('score'),
                    opp.get('confidence'),
                    json.dumps(opp.get('fits', []), ensure_ascii=False),
                    json.dumps(opp.get('gaps', []), ensure_ascii=False),
                    opp.get('angle'),
                    opp.get('status', 'scored'),
                    opp.get('id')
                ))
                if cursor.rowcount > 0:
                    saved_count += 1
            except Exception as e:
                print(f"[score] DB error saving opportunity {opp.get('id')}: {e}")
        
        conn.commit()
        conn.close()
        print(f"[score] Saved {saved_count}/{len(opportunities)} opportunities to database")
        return saved_count
    
    def record_feedback(self, opportunity_id: str, rating: str, notes: str = ""):
        """Record 👍/👎 feedback for learning.
        
        Args:
            opportunity_id: ID of the opportunity being rated
            rating: 'up' (👍) or 'down' (👎)
            notes: Optional notes about why this rating was given
        """
        entry = {
            'opportunity_id': opportunity_id,
            'rating': rating,
            'notes': notes,
            'timestamp': datetime.now().isoformat()
        }
        
        # Extract pattern from opportunity if available
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute(
            "SELECT title, company, description FROM opportunities WHERE id = ?",
            (opportunity_id,)
        )
        row = cursor.fetchone()
        conn.close()
        
        if row:
            title, company, desc = row
            entry['opportunity_preview'] = f"{title} @ {company}"
            # Extract key terms for pattern learning
            entry['pattern'] = notes or f"Rated {rating} for {title} role"
        
        if rating == 'up':
            self.feedback['thumbs_up'].append(entry)
        else:
            self.feedback['thumbs_down'].append(entry)
        
        # Save feedback to file
        try:
            with open(self.feedback_path, 'w', encoding='utf-8') as f:
                json.dump(self.feedback, f, indent=2, ensure_ascii=False)
            print(f"[score] Recorded {rating} feedback for {opportunity_id}")
        except IOError as e:
            print(f"[score] Error saving feedback: {e}")
    
    def get_feedback_stats(self) -> Dict:
        """Get statistics about recorded feedback.
        
        Returns:
            Dictionary with feedback counts and patterns
        """
        return {
            'total_up': len(self.feedback.get('thumbs_up', [])),
            'total_down': len(self.feedback.get('thumbs_down', [])),
            'recent_up': self.feedback.get('thumbs_up', [])[-5:],
            'recent_down': self.feedback.get('thumbs_down', [])[-5:]
        }
    
    def process_pending_opportunities(self, limit: int = None) -> List[Dict]:
        """Main workflow: fetch unscored opportunities, score them, save results.
        
        Args:
            limit: Maximum number of opportunities to process
            
        Returns:
            List of scored opportunity dictionaries
        """
        print(f"[score] Fetching unscored opportunities...")
        opportunities = self.get_unscored_opportunities(limit=limit)
        
        if not opportunities:
            print("[score] No unscored opportunities found")
            return []
        
        print(f"[score] Found {len(opportunities)} opportunities to score")
        
        # Score all opportunities
        scored = self.score_batch(opportunities)
        
        # Save results to database
        self.save_scored_opportunities(scored)
        
        # Print summary
        high_matches = [o for o in scored if o.get('score', 0) >= self.preferences.get('high_score_threshold', 80)]
        medium_matches = [o for o in scored if 60 <= o.get('score', 0) < self.preferences.get('high_score_threshold', 80)]
        low_matches = [o for o in scored if o.get('score', 0) < 60]
        
        print(f"\n[score] Summary:")
        print(f"  High matches (80+): {len(high_matches)}")
        print(f"  Medium matches (60-79): {len(medium_matches)}")
        print(f"  Low matches (<60): {len(low_matches)}")
        
        return scored


# Convenience function for direct usage
def score_opportunities(config: dict = None, db_path: str = None, limit: int = None) -> List[Dict]:
    """Convenience function to score pending opportunities.
    
    Args:
        config: Configuration dictionary
        db_path: Path to database
        limit: Maximum number to process
        
    Returns:
        List of scored opportunities
    """
    scorer = OpportunityScorer(config=config, db_path=db_path)
    return scorer.process_pending_opportunities(limit=limit)


if __name__ == "__main__":
    # Test the scoring functionality
    print("=" * 60)
    print("Opportunity Scorer - Test Mode")
    print("=" * 60)
    
    # Initialize scorer
    scorer = OpportunityScorer()
    
    # Test with sample opportunity
    test_op = {
        'id': 'test_001',
        'title': 'AI Product Manager - Education Tech',
        'company': 'TestCorp',
        'location': 'Beijing',
        'description': '''We are looking for an AI Product Manager to lead our education technology initiatives.
        
Requirements:
- 1+ years of product management experience
- Understanding of AI/ML technologies
- Experience in education or EdTech preferred
- Strong communication skills
- Ability to work in a fast-paced environment

Responsibilities:
- Define product strategy for AI-powered learning tools
- Collaborate with engineering and design teams
- Conduct user research and analyze metrics
- Drive product roadmap and execution

Nice to have:
- Content creation experience
- Photography skills
- Vibe Coding mindset''',
        'salary': '30-50k',
        'source': 'test'
    }
    
    print("\n--- Testing Single Opportunity Scoring ---")
    result = scorer.score_opportunity(test_op)
    print(f"\nScore: {result.score}/100 ({result.confidence} confidence)")
    print(f"Fits:")
    for fit in result.fits:
        print(f"  ✓ {fit}")
    print(f"Gaps:")
    for gap in result.gaps:
        print(f"  ⚠ {gap}")
    print(f"Angle: {result.angle}")
    
    # Test batch processing
    print("\n--- Testing Batch Processing ---")
    test_ops = [
        test_op,
        {
            'id': 'test_002',
            'title': 'Senior Backend Engineer',
            'company': 'BigTech',
            'location': 'Shanghai',
            'description': 'Looking for senior backend engineer with 5+ years Java experience. Microservices architecture.',
            'salary': '50-80k',
            'source': 'test'
        },
        {
            'id': 'test_003',
            'title': 'AI Education Specialist',
            'company': 'EduStartup',
            'location': 'Remote',
            'description': 'Join us to build AI tutors for K-12 students. Looking for someone passionate about education and AI.',
            'salary': '25-40k',
            'source': 'test'
        }
    ]
    
    results = scorer.score_batch(test_ops)
    
    print("\n--- Batch Results ---")
    for r in results:
        print(f"{r['title'][:40]:<40} | Score: {r['score']:>3}/100 | {r['confidence']}")
    
    # Test feedback recording
    print("\n--- Testing Feedback Recording ---")
    scorer.record_feedback('test_001', 'up', 'Great match for my background!')
    scorer.record_feedback('test_002', 'down', 'Too technical, not a good fit')
    
    stats = scorer.get_feedback_stats()
    print(f"\nFeedback Stats: {stats['total_up']} up, {stats['total_down']} down")
    
    print("\n" + "=" * 60)
    print("Test Complete!")
    print("=" * 60)
