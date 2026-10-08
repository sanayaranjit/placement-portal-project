def get_fit_score(student, drive):
    s_skills = set(s.strip().lower() for s in (student.skills or "").split(',')) - {''}
    j_skills = set(s.strip().lower() for s in (drive.required_skills or "").split(',')) - {''}
    
    j_streams = [s.strip().lower() for s in (drive.preferred_streams or "").split(',') if s.strip()]
    student_dept = student.department.lower() if student.department else ""
    

    skill_points = 0.0
    other_points = 0.0
    factors = []
    

    if not j_skills:
        skill_points = 50.0
        skill_match_pct = 100.0
        factors.append(("✅ Skills", "No specific requirements (50/50)"))
    else:
        skill_match_pct = round((len(s_skills & j_skills) / len(j_skills)) * 100, 1)
        skill_points = (skill_match_pct / 100) * 50
        
        if skill_match_pct >= 80:
            factors.append(("✅ Skills", f"{skill_match_pct}% match ({skill_points:.1f}/50)"))
        elif skill_match_pct >= 50:
            factors.append(("⚠️ Skills", f"{skill_match_pct}% match - Minor gap ({skill_points:.1f}/50)"))
        else:
            factors.append(("❌ Skills", f"{skill_match_pct}% match - Major gap ({skill_points:.1f}/50)"))


    exp_points = 0.0
    j_proj = drive.min_projects or 0
    j_int = drive.min_internships or 0
    s_proj = student.projects or 0
    s_int = student.internships or 0

    if j_int > 0:
        int_ratio = min(s_int / j_int, 1.0) 
        exp_points += int_ratio * 15
    else:
        exp_points += 15 if s_int >= 1 else 5

    if j_proj > 0:
        proj_ratio = min(s_proj / j_proj, 1.0)
        exp_points += proj_ratio * 10
    else:
        exp_points += 10 if s_proj >= 2 else (5 if s_proj >= 1 else 0)

    if exp_points >= 20:
        factors.append(("✅ Experience", f"Strong practical background ({exp_points:.1f}/25)"))
    elif exp_points >= 12:
        factors.append(("⚠️ Experience", f"Decent experience, could be stronger ({exp_points:.1f}/25)"))
    else:
        factors.append(("❌ Experience", f"Lacks practical projects/internships ({exp_points:.1f}/25)"))
        
    other_points += exp_points


    j_cgpa = drive.min_cgpa or 6.0
    s_cgpa = student.cgpa or 0.0
    if s_cgpa >= j_cgpa:
        other_points += 15
        factors.append(("✅ CGPA", f"Meets {j_cgpa} req (Yours: {s_cgpa}) (15/15)"))
    else:
        cgpa_pts = round(max(0, (s_cgpa / j_cgpa) * 15), 1)
        other_points += cgpa_pts
        factors.append(("❌ CGPA", f"Below {j_cgpa} req (Yours: {s_cgpa}) ({cgpa_pts}/15)"))


    if not j_streams:
        other_points += 5
        dept_name = student.department if student.department else "Not Specified"
        factors.append(("✅ Branch", f"Open to all branches ({dept_name}) (5/5)"))
    elif student_dept in j_streams:
        other_points += 5
        factors.append(("✅ Branch", f"{student.department} is preferred (5/5)"))
    else:
        other_points += 1 
        factors.append(("⚠️ Branch", f"{student.department if student.department else 'Not Specified'} not preferred (1/5)"))


    j_backlogs = drive.max_backlogs if drive.max_backlogs is not None else 99
    s_backlogs = student.backlogs or 0
    if s_backlogs <= j_backlogs:
        other_points += 5
        factors.append(("✅ Backlogs", f"Within limit ({s_backlogs} allowed: {j_backlogs}) (5/5)"))
    else:
        other_points += 0
        factors.append(("❌ Backlogs", f"Exceeds limit ({s_backlogs} limit: {j_backlogs}) (0/5)"))


    if not j_skills:
        multiplier = 1.0 
    elif skill_match_pct < 30.0:
        multiplier = 0.2 
    elif skill_match_pct < 60.0:
        multiplier = 0.5 
    else:
        multiplier = 1.0 

    final_other_points = other_points * multiplier
    

    final_score = round(skill_points + final_other_points, 1)
    final_score = max(0.0, min(100.0, final_score))
    
    if final_score >= 75: 
        message = "Excellent fit! Highly recommended to apply."
    elif final_score >= 55: 
        message = "Good fit, but address the gaps before interviewing."
    elif final_score >= 35: 
        message = "Moderate fit. You may struggle with the requirements."
    else: 
        message = "Low fit. This role does not match your current profile."
        
    return final_score, message, factors