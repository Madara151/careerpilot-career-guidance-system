-- phpMyAdmin SQL Dump
-- version 5.2.1
-- https://www.phpmyadmin.net/
--
-- Host: 127.0.0.1
-- Generation Time: Aug 20, 2026 at 09:30 PM
-- Server version: 10.4.32-MariaDB
-- PHP Version: 8.0.30

SET SQL_MODE = "NO_AUTO_VALUE_ON_ZERO";
START TRANSACTION;
SET time_zone = "+00:00";


/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!40101 SET NAMES utf8mb4 */;

--
-- Database: `careerpilot`
--

-- --------------------------------------------------------

--
-- Table structure for table `careers`
--

CREATE TABLE `careers` (
  `career_id` int(11) NOT NULL,
  `career_name` varchar(100) NOT NULL,
  `description` text DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Dumping data for table `careers`
--

INSERT INTO `careers` (`career_id`, `career_name`, `description`) VALUES
(1, 'Software Engineer', 'Design and develop software applications'),
(2, 'Data Engineer', 'Build and manage data pipelines'),
(3, 'Data Scientist', 'Analyze and predict using data'),
(4, 'AI Engineer', 'Develop artificial intelligence solutions'),
(5, 'Cybersecurity Analyst', 'Protect systems and networks'),
(6, 'Cloud Engineer', 'Manage cloud infrastructure'),
(7, 'DevOps Engineer', 'Automate deployment processes'),
(8, 'UI/UX Designer', 'Design user interfaces and experiences');

-- --------------------------------------------------------

--
-- Table structure for table `career_skills`
--

CREATE TABLE `career_skills` (
  `career_skill_id` int(11) NOT NULL,
  `career_id` int(11) NOT NULL,
  `skill_id` int(11) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Dumping data for table `career_skills`
--

INSERT INTO `career_skills` (`career_skill_id`, `career_id`, `skill_id`) VALUES
(1, 1, 1),
(2, 1, 2),
(3, 1, 3),
(4, 1, 6),
(5, 1, 8),
(6, 2, 1),
(7, 2, 3),
(10, 2, 8),
(9, 2, 10),
(8, 2, 20),
(11, 3, 1),
(12, 3, 3),
(13, 3, 21),
(14, 3, 23),
(15, 3, 24),
(16, 4, 1),
(20, 4, 10),
(17, 4, 21),
(18, 4, 22),
(19, 4, 23),
(22, 5, 3),
(23, 5, 8),
(24, 5, 9),
(21, 5, 10),
(25, 5, 26),
(30, 6, 8),
(26, 6, 9),
(29, 6, 10),
(27, 6, 28),
(28, 6, 30),
(33, 7, 8),
(31, 7, 9),
(32, 7, 10),
(35, 7, 20),
(34, 7, 32),
(36, 8, 4),
(37, 8, 5),
(38, 8, 6),
(39, 8, 7),
(40, 8, 33);

-- --------------------------------------------------------

--
-- Table structure for table `contact_messages`
--

CREATE TABLE `contact_messages` (
  `message_id` int(11) NOT NULL,
  `full_name` varchar(100) NOT NULL,
  `email` varchar(100) NOT NULL,
  `subject` varchar(150) DEFAULT NULL,
  `message` text NOT NULL,
  `submitted_at` timestamp NOT NULL DEFAULT current_timestamp(),
  `is_read` tinyint(1) NOT NULL DEFAULT 0
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Dumping data for table `contact_messages`
--

INSERT INTO `contact_messages` (`message_id`, `full_name`, `email`, `subject`, `message`, `submitted_at`, `is_read`) VALUES
(1, 'pasindu', 'p@gmail.com', 'career', 'Can I get more courses like this?', '2026-08-20 07:02:12', 1);

-- --------------------------------------------------------

--
-- Table structure for table `courses`
--

CREATE TABLE `courses` (
  `course_id` int(11) NOT NULL,
  `course_name` varchar(150) NOT NULL,
  `provider` varchar(100) DEFAULT NULL,
  `course_link` varchar(255) DEFAULT NULL,
  `description` text DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Dumping data for table `courses`
--

INSERT INTO `courses` (`course_id`, `course_name`, `provider`, `course_link`, `description`) VALUES
(1, 'Python for Everybody', 'Coursera', 'https://www.coursera.org/specializations/python', 'Beginner-friendly introduction to Python programming and data structures.'),
(2, 'SQL for Data Science', 'Coursera', 'https://www.coursera.org/learn/sql-for-data-science', 'Learn to write SQL queries to explore and analyze data.'),
(3, 'Git & GitHub Crash Course', 'freeCodeCamp', 'https://www.freecodecamp.org/news/git-and-github-crash-course/', 'Hands-on guide to version control with Git and collaboration on GitHub.'),
(4, 'Machine Learning Specialization', 'Coursera (DeepLearning.AI)', 'https://www.coursera.org/specializations/machine-learning-introduction', 'Foundational course covering supervised and unsupervised learning.'),
(5, 'Statistics with Python', 'Coursera', 'https://www.coursera.org/learn/statistics-with-python', 'Descriptive and inferential statistics using Python.'),
(6, 'Power BI for Beginners', 'Microsoft Learn', 'https://learn.microsoft.com/en-us/training/powerplatform/power-bi', 'Build interactive dashboards and reports using Power BI.'),
(7, 'AWS Cloud Practitioner Essentials', 'AWS Skill Builder', 'https://skillbuilder.aws/', 'Introductory course covering core AWS cloud concepts.'),
(8, 'Linux Command Line Basics', 'Codecademy', 'https://www.codecademy.com/learn/learn-the-command-line', 'Learn to navigate and use the Linux command line.'),
(9, 'Microsoft Azure Fundamentals (AZ-900)', 'Microsoft Learn', 'https://learn.microsoft.com/en-us/certifications/azure-fundamentals/', 'Core Azure concepts, services, and cloud fundamentals.'),
(10, 'JavaScript Basics', 'freeCodeCamp', 'https://www.freecodecamp.org/learn/javascript-algorithms-and-data-structures/', 'Learn JavaScript fundamentals for interactive web development.'),
(11, 'React - The Complete Guide', 'Udemy', 'https://www.udemy.com/course/react-the-complete-guide-incl-redux/', 'Build modern, component-based frontend applications with React.'),
(12, 'Introduction to Cybersecurity', 'Cisco Networking Academy', 'https://www.netacad.com/courses/cybersecurity/introduction-cybersecurity', 'Foundational cybersecurity concepts and best practices.');

-- --------------------------------------------------------

--
-- Table structure for table `learning_roadmaps`
--

CREATE TABLE `learning_roadmaps` (
  `roadmap_id` int(11) NOT NULL,
  `career_id` int(11) NOT NULL,
  `profile_id` int(11) DEFAULT NULL,
  `step_no` int(11) NOT NULL,
  `title` varchar(200) NOT NULL,
  `description` text DEFAULT NULL,
  `status` enum('Not Started','In Progress','Completed') DEFAULT 'Not Started'
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- --------------------------------------------------------

--
-- Table structure for table `progress_tracking`
--

CREATE TABLE `progress_tracking` (
  `progress_id` int(11) NOT NULL,
  `profile_id` int(11) NOT NULL,
  `skill_id` int(11) NOT NULL,
  `completion_percentage` int(11) DEFAULT 0,
  `completed_date` date DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- --------------------------------------------------------

--
-- Table structure for table `resumes`
--

CREATE TABLE `resumes` (
  `resume_id` int(11) NOT NULL,
  `profile_id` int(11) NOT NULL,
  `file_name` varchar(255) NOT NULL,
  `update_date` datetime DEFAULT current_timestamp() ON UPDATE current_timestamp()
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Dumping data for table `resumes`
--

INSERT INTO `resumes` (`resume_id`, `profile_id`, `file_name`, `update_date`) VALUES
(15, 1, '1_20260814200314.pdf', '2026-08-14 20:03:14');

-- --------------------------------------------------------

--
-- Table structure for table `skills`
--

CREATE TABLE `skills` (
  `skill_id` int(11) NOT NULL,
  `skill_name` varchar(100) NOT NULL,
  `category` varchar(100) DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Dumping data for table `skills`
--

INSERT INTO `skills` (`skill_id`, `skill_name`, `category`) VALUES
(1, 'Python', 'Programming'),
(2, 'Java', 'Programming'),
(3, 'SQL', 'Database'),
(4, 'HTML', 'Web Development'),
(5, 'CSS', 'Web Development'),
(6, 'JavaScript', 'Web Development'),
(7, 'React', 'Frontend'),
(8, 'Git', 'Version Control'),
(9, 'AWS', 'Cloud'),
(10, 'Linux', 'Operating System'),
(13, 'C#', 'Programming'),
(14, 'PHP', 'Programming'),
(20, 'MySQL', 'Database'),
(21, 'Machine Learning', 'Data Science'),
(22, 'Data Analysis', 'Data Science'),
(23, 'Statistics', 'Data Science'),
(24, 'Power BI', 'Data Science'),
(25, 'Tableau', 'Data Science'),
(26, 'Cyber Security', 'Security'),
(27, 'Network Security', 'Security'),
(28, 'Cloud Computing', 'Cloud'),
(30, 'Azure', 'Cloud'),
(32, 'GitHub', 'Tools'),
(33, 'Communication', 'Soft Skills'),
(34, 'Problem Solving', 'Soft Skills'),
(35, 'Teamwork', 'Soft Skills');

-- --------------------------------------------------------

--
-- Table structure for table `skill_courses`
--

CREATE TABLE `skill_courses` (
  `id` int(11) NOT NULL,
  `skill_id` int(11) NOT NULL,
  `course_id` int(11) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Dumping data for table `skill_courses`
--

INSERT INTO `skill_courses` (`id`, `skill_id`, `course_id`) VALUES
(1, 1, 1),
(2, 3, 2),
(3, 8, 3),
(4, 32, 3),
(5, 21, 4),
(6, 23, 5),
(7, 24, 6),
(8, 9, 7),
(9, 10, 8),
(10, 30, 9),
(11, 28, 9),
(12, 6, 10),
(13, 7, 11),
(14, 26, 12);

-- --------------------------------------------------------

--
-- Table structure for table `student_profiles`
--

CREATE TABLE `student_profiles` (
  `profile_id` int(11) NOT NULL,
  `user_id` int(11) NOT NULL,
  `university` varchar(150) DEFAULT NULL,
  `degree` varchar(150) DEFAULT NULL,
  `years_of_study` int(11) DEFAULT NULL,
  `target_career_id` int(11) DEFAULT NULL,
  `bio` text DEFAULT NULL,
  `profile_picture` varchar(255) DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Dumping data for table `student_profiles`
--

INSERT INTO `student_profiles` (`profile_id`, `user_id`, `university`, `degree`, `years_of_study`, `target_career_id`, `bio`, `profile_picture`) VALUES
(1, 2, 'ICBT', 'BSc', 3, 1, 'Software Engineer', 'profile_1_20260814202635.jpg'),
(2, 3, 'ICBT', 'BSc', 1, NULL, NULL, NULL),
(3, 4, 'ICBT', 'BSc', 4, NULL, NULL, NULL);

-- --------------------------------------------------------

--
-- Table structure for table `student_skills`
--

CREATE TABLE `student_skills` (
  `student_skill_id` int(11) NOT NULL,
  `profile_id` int(11) NOT NULL,
  `skill_id` int(11) NOT NULL,
  `proficiency_level` enum('Beginner','Intermediate','Advanced') DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Dumping data for table `student_skills`
--

INSERT INTO `student_skills` (`student_skill_id`, `profile_id`, `skill_id`, `proficiency_level`) VALUES
(64, 1, 2, NULL),
(65, 1, 6, NULL),
(66, 1, 14, NULL),
(67, 1, 1, NULL),
(68, 1, 3, NULL),
(69, 1, 8, NULL);

-- --------------------------------------------------------

--
-- Table structure for table `users`
--

CREATE TABLE `users` (
  `user_id` int(11) NOT NULL,
  `full_name` varchar(100) NOT NULL,
  `email` varchar(100) NOT NULL,
  `password` varchar(255) NOT NULL,
  `role` enum('admin','student') NOT NULL DEFAULT 'student',
  `created_at` timestamp NOT NULL DEFAULT current_timestamp()
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Dumping data for table `users`
--

INSERT INTO `users` (`user_id`, `full_name`, `email`, `password`, `role`, `created_at`) VALUES
(1, 'System Admin', 'admin@careerpilot.com', 'scrypt:32768:8:1$nL60podBAHuVnLb0$d1124bdd301738b11f6c246bfaf208343eaf2c12d7c617079d066e9a1e6b37a5b5f956cb687bd65230c72001a41ba1594e67377c954b73ddb121c784e8e6a540', 'admin', '2026-07-05 16:53:39'),
(2, 'pasindu madara', 'p@gmail.com', 'scrypt:32768:8:1$H75ia6KlZDhn2NfZ$4e34c4c9ad0a6d8bf17c2f795a00582e211627049f482c7fcc0b706c5a138b4a9bd8f55171bfe85c8827d16494a736eaf8e2f92401574515d675106eeebf3bca', 'student', '2026-07-05 16:56:21'),
(3, 'madara', 'm@gmail.com', 'scrypt:32768:8:1$yYzaYC7WzTMu5gfy$5cc7077f8d5623c4c6cc4e43ffe770e84070385c62e20f32a2ec11a5cef8916adcb02b2e0577f0b52d34144e1b37352afd826d69139f2fa55eb9f3fc6fd302fa', 'student', '2026-08-20 09:57:04'),
(4, 'tilak', 't@gmail.com', 'scrypt:32768:8:1$2Vy9ou91pVs2arZO$9e99b91e433b0c6a993a8c2ec4368efdbee03419d0caf5b124df3a3e35e778ed32eca7c001ae315a976f60220fd8e4af2dc85f09f1dcf1f06af6716ec9b1deba', 'student', '2026-08-20 10:00:29');

--
-- Indexes for dumped tables
--

--
-- Indexes for table `careers`
--
ALTER TABLE `careers`
  ADD PRIMARY KEY (`career_id`);

--
-- Indexes for table `career_skills`
--
ALTER TABLE `career_skills`
  ADD PRIMARY KEY (`career_skill_id`),
  ADD UNIQUE KEY `unique_career_skill` (`career_id`,`skill_id`),
  ADD KEY `fk_career_skill_skill` (`skill_id`);

--
-- Indexes for table `contact_messages`
--
ALTER TABLE `contact_messages`
  ADD PRIMARY KEY (`message_id`);

--
-- Indexes for table `courses`
--
ALTER TABLE `courses`
  ADD PRIMARY KEY (`course_id`);

--
-- Indexes for table `learning_roadmaps`
--
ALTER TABLE `learning_roadmaps`
  ADD PRIMARY KEY (`roadmap_id`),
  ADD KEY `fk_roadmap_career` (`career_id`),
  ADD KEY `fk_roadmap_profile` (`profile_id`);

--
-- Indexes for table `progress_tracking`
--
ALTER TABLE `progress_tracking`
  ADD PRIMARY KEY (`progress_id`),
  ADD KEY `fk_progress_profile` (`profile_id`),
  ADD KEY `fk_progress_skill` (`skill_id`);

--
-- Indexes for table `resumes`
--
ALTER TABLE `resumes`
  ADD PRIMARY KEY (`resume_id`),
  ADD KEY `fk_resume_profile` (`profile_id`);

--
-- Indexes for table `skills`
--
ALTER TABLE `skills`
  ADD PRIMARY KEY (`skill_id`);

--
-- Indexes for table `skill_courses`
--
ALTER TABLE `skill_courses`
  ADD PRIMARY KEY (`id`),
  ADD KEY `fk_skill_course_skill` (`skill_id`),
  ADD KEY `fk_skill_course_course` (`course_id`);

--
-- Indexes for table `student_profiles`
--
ALTER TABLE `student_profiles`
  ADD PRIMARY KEY (`profile_id`),
  ADD KEY `fk_profile_user` (`user_id`),
  ADD KEY `fk_target_career` (`target_career_id`);

--
-- Indexes for table `student_skills`
--
ALTER TABLE `student_skills`
  ADD PRIMARY KEY (`student_skill_id`),
  ADD KEY `fk_student_skill_profile` (`profile_id`),
  ADD KEY `fk_student_skill_skill` (`skill_id`);

--
-- Indexes for table `users`
--
ALTER TABLE `users`
  ADD PRIMARY KEY (`user_id`),
  ADD UNIQUE KEY `email` (`email`);

--
-- AUTO_INCREMENT for dumped tables
--

--
-- AUTO_INCREMENT for table `careers`
--
ALTER TABLE `careers`
  MODIFY `career_id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=10;

--
-- AUTO_INCREMENT for table `career_skills`
--
ALTER TABLE `career_skills`
  MODIFY `career_skill_id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=42;

--
-- AUTO_INCREMENT for table `contact_messages`
--
ALTER TABLE `contact_messages`
  MODIFY `message_id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=2;

--
-- AUTO_INCREMENT for table `courses`
--
ALTER TABLE `courses`
  MODIFY `course_id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=14;

--
-- AUTO_INCREMENT for table `learning_roadmaps`
--
ALTER TABLE `learning_roadmaps`
  MODIFY `roadmap_id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=180;

--
-- AUTO_INCREMENT for table `progress_tracking`
--
ALTER TABLE `progress_tracking`
  MODIFY `progress_id` int(11) NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT for table `resumes`
--
ALTER TABLE `resumes`
  MODIFY `resume_id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=16;

--
-- AUTO_INCREMENT for table `skills`
--
ALTER TABLE `skills`
  MODIFY `skill_id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=37;

--
-- AUTO_INCREMENT for table `skill_courses`
--
ALTER TABLE `skill_courses`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=18;

--
-- AUTO_INCREMENT for table `student_profiles`
--
ALTER TABLE `student_profiles`
  MODIFY `profile_id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=4;

--
-- AUTO_INCREMENT for table `student_skills`
--
ALTER TABLE `student_skills`
  MODIFY `student_skill_id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=71;

--
-- AUTO_INCREMENT for table `users`
--
ALTER TABLE `users`
  MODIFY `user_id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=5;

--
-- Constraints for dumped tables
--

--
-- Constraints for table `career_skills`
--
ALTER TABLE `career_skills`
  ADD CONSTRAINT `fk_career_skill_career` FOREIGN KEY (`career_id`) REFERENCES `careers` (`career_id`) ON DELETE CASCADE,
  ADD CONSTRAINT `fk_career_skill_skill` FOREIGN KEY (`skill_id`) REFERENCES `skills` (`skill_id`) ON DELETE CASCADE;

--
-- Constraints for table `learning_roadmaps`
--
ALTER TABLE `learning_roadmaps`
  ADD CONSTRAINT `fk_roadmap_career` FOREIGN KEY (`career_id`) REFERENCES `careers` (`career_id`) ON DELETE CASCADE,
  ADD CONSTRAINT `fk_roadmap_profile` FOREIGN KEY (`profile_id`) REFERENCES `student_profiles` (`profile_id`) ON DELETE CASCADE;

--
-- Constraints for table `progress_tracking`
--
ALTER TABLE `progress_tracking`
  ADD CONSTRAINT `fk_progress_profile` FOREIGN KEY (`profile_id`) REFERENCES `student_profiles` (`profile_id`) ON DELETE CASCADE,
  ADD CONSTRAINT `fk_progress_skill` FOREIGN KEY (`skill_id`) REFERENCES `skills` (`skill_id`) ON DELETE CASCADE;

--
-- Constraints for table `resumes`
--
ALTER TABLE `resumes`
  ADD CONSTRAINT `fk_resume_profile` FOREIGN KEY (`profile_id`) REFERENCES `student_profiles` (`profile_id`) ON DELETE CASCADE;

--
-- Constraints for table `skill_courses`
--
ALTER TABLE `skill_courses`
  ADD CONSTRAINT `fk_skill_course_course` FOREIGN KEY (`course_id`) REFERENCES `courses` (`course_id`) ON DELETE CASCADE,
  ADD CONSTRAINT `fk_skill_course_skill` FOREIGN KEY (`skill_id`) REFERENCES `skills` (`skill_id`) ON DELETE CASCADE;

--
-- Constraints for table `student_profiles`
--
ALTER TABLE `student_profiles`
  ADD CONSTRAINT `fk_profile_user` FOREIGN KEY (`user_id`) REFERENCES `users` (`user_id`) ON DELETE CASCADE,
  ADD CONSTRAINT `fk_target_career` FOREIGN KEY (`target_career_id`) REFERENCES `careers` (`career_id`) ON DELETE SET NULL;

--
-- Constraints for table `student_skills`
--
ALTER TABLE `student_skills`
  ADD CONSTRAINT `fk_student_skill_profile` FOREIGN KEY (`profile_id`) REFERENCES `student_profiles` (`profile_id`) ON DELETE CASCADE,
  ADD CONSTRAINT `fk_student_skill_skill` FOREIGN KEY (`skill_id`) REFERENCES `skills` (`skill_id`) ON DELETE CASCADE;
COMMIT;

/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
