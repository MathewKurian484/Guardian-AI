import { motion } from 'framer-motion';
import { Link } from 'react-router-dom';
import { Shield, MessageSquare, Zap } from 'lucide-react';

const Dashboard = () => {
  const features = [
    {
      icon: Shield,
      title: 'Code Audit',
      description: 'Scan repositories for compliance violations',
      gradient: 'from-red-500 to-orange-500',
      link: '/audit',
      badge: 'Popular',
    },
    {
      icon: MessageSquare,
      title: 'Q&A Assistant',
      description: 'Ask questions about your codebase',
      gradient: 'from-blue-500 to-cyan-500',
      link: '/qa',
      badge: 'Smart',
    },
  ];

  return (
    <div className="min-h-screen p-8 relative overflow-hidden">
      {/* Animated Background Gradient */}
      <div className="fixed inset-0 -z-10 overflow-hidden">
        <motion.div
          animate={{
            backgroundPosition: ['0% 0%', '100% 100%'],
          }}
          transition={{
            duration: 20,
            repeat: Infinity,
            repeatType: 'reverse',
          }}
          className="absolute inset-0 bg-gradient-to-br from-primary-50 via-accent-50 to-primary-100 dark:from-slate-950 dark:via-primary-950 dark:to-slate-900 opacity-50"
          style={{ backgroundSize: '400% 400%' }}
        />
        
        {/* Floating Orbs */}
        <motion.div
          animate={{
            x: [0, 100, 0],
            y: [0, -100, 0],
            scale: [1, 1.2, 1],
          }}
          transition={{
            duration: 15,
            repeat: Infinity,
            ease: 'easeInOut',
          }}
          className="absolute top-20 left-20 w-96 h-96 bg-primary-400/20 dark:bg-primary-500/10 rounded-full blur-3xl"
        />
        <motion.div
          animate={{
            x: [0, -100, 0],
            y: [0, 100, 0],
            scale: [1, 1.3, 1],
          }}
          transition={{
            duration: 18,
            repeat: Infinity,
            ease: 'easeInOut',
          }}
          className="absolute bottom-20 right-20 w-96 h-96 bg-accent-400/20 dark:bg-accent-500/10 rounded-full blur-3xl"
        />
        <motion.div
          animate={{
            x: [0, 80, 0],
            y: [0, -80, 0],
            scale: [1, 1.1, 1],
          }}
          transition={{
            duration: 12,
            repeat: Infinity,
            ease: 'easeInOut',
          }}
          className="absolute top-1/2 left-1/2 w-96 h-96 bg-primary-300/20 dark:bg-primary-600/10 rounded-full blur-3xl"
        />
      </div>

      {/* Grid Pattern Overlay */}
      <div className="fixed inset-0 -z-10">
        <div className="absolute inset-0 bg-grid-pattern opacity-5 dark:opacity-10" />
      </div>
      {/* Hero Section */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        className="text-center mb-16 relative z-10"
      >
        <motion.div
          initial={{ scale: 0 }}
          animate={{ scale: 1 }}
          transition={{ delay: 0.2, type: 'spring', stiffness: 200 }}
          className="inline-flex items-center gap-2 px-4 py-2 rounded-full bg-primary-100 dark:bg-primary-900/30 mb-6 backdrop-blur-sm border border-primary-200 dark:border-primary-800"
        >
          <motion.div
            animate={{ rotate: 360 }}
            transition={{ duration: 3, repeat: Infinity, ease: 'linear' }}
          >
            <Zap className="w-4 h-4 text-primary-600 dark:text-primary-400" />
          </motion.div>
          <span className="text-sm font-semibold text-primary-600 dark:text-primary-400">
            Powered by AI
          </span>
        </motion.div>

        <motion.h1
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.3 }}
          className="text-6xl font-bold mb-6"
        >
          <span className="gradient-text">Guardian AI</span>
        </motion.h1>
        <motion.p
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 0.4 }}
          className="text-xl text-gray-600 dark:text-slate-400 max-w-2xl mx-auto"
        >
          Your intelligent compliance and code analysis platform. Detect
          violations, understand codebases, and ensure regulatory compliance.
        </motion.p>
      </motion.div>

      {/* Feature Cards */}
      <div className="grid md:grid-cols-2 gap-8 mb-16 max-w-4xl mx-auto relative z-10">
        {features.map((feature, index) => (
          <motion.div
            key={feature.title}
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: index * 0.1 + 0.5 }}
            whileHover={{ y: -8 }}
          >
            <Link to={feature.link}>
              <div className="card group cursor-pointer relative overflow-hidden">
                {/* Hover Glow Effect */}
                <div className={`absolute inset-0 bg-gradient-to-br ${feature.gradient} opacity-0 group-hover:opacity-10 transition-opacity duration-300`} />
                
                {/* Badge */}
                <div className="absolute top-4 right-4 px-3 py-1 rounded-full bg-primary-100 dark:bg-primary-900/50 text-xs font-semibold text-primary-600 dark:text-primary-400 opacity-0 group-hover:opacity-100 transition-opacity">
                  {feature.badge}
                </div>

                <motion.div
                  whileHover={{ rotate: [0, -10, 10, 0], scale: 1.1 }}
                  transition={{ duration: 0.5 }}
                  className={`w-16 h-16 rounded-2xl bg-gradient-to-br ${feature.gradient} 
                  flex items-center justify-center mb-4 shadow-lg group-hover:shadow-2xl transition-all relative`}
                >
                  <div className={`absolute inset-0 bg-gradient-to-br ${feature.gradient} rounded-2xl blur-xl opacity-50 group-hover:opacity-75 transition-opacity`} />
                  <feature.icon className="w-8 h-8 text-white relative z-10" />
                </motion.div>

                <h3 className="text-2xl font-bold mb-2 text-gray-900 dark:text-slate-50 group-hover:text-primary-600 dark:group-hover:text-primary-400 transition-colors">
                  {feature.title}
                </h3>
                <p className="text-gray-600 dark:text-slate-400 mb-4">
                  {feature.description}
                </p>

                {/* Arrow on Hover */}
                <div className="flex items-center gap-2 text-primary-600 dark:text-primary-400 font-medium opacity-0 group-hover:opacity-100 transition-opacity">
                  <span>Get Started</span>
                  <motion.svg
                    xmlns="http://www.w3.org/2000/svg"
                    width="16"
                    height="16"
                    viewBox="0 0 24 24"
                    fill="none"
                    stroke="currentColor"
                    strokeWidth="2"
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    animate={{ x: [0, 4, 0] }}
                    transition={{ duration: 1.5, repeat: Infinity }}
                  >
                    <path d="M5 12h14M12 5l7 7-7 7" />
                  </motion.svg>
                </div>
              </div>
            </Link>
          </motion.div>
        ))}
      </div>

      {/* Quick Start Guide */}
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ delay: 0.8 }}
        className="max-w-4xl mx-auto mt-16 relative z-10"
      >
        <h2 className="text-3xl font-bold text-center mb-8 text-gray-900 dark:text-slate-50">
          How It Works
        </h2>
        <div className="grid md:grid-cols-3 gap-6">
          {[
            {
              step: 1,
              title: 'Choose Analysis Type',
              description: 'Select code audit or Q&A mode',
            },
            {
              step: 2,
              title: 'Input Repository',
              description: 'Provide GitHub URL and compliance documents',
            },
            {
              step: 3,
              title: 'Get Insights',
              description: 'Receive detailed analysis and recommendations',
            },
          ].map((item, index) => (
            <motion.div
              key={item.step}
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.9 + index * 0.1 }}
              whileHover={{ scale: 1.05 }}
              className="text-center"
            >
              <motion.div
                whileHover={{ rotate: 360 }}
                transition={{ duration: 0.6 }}
                className="w-12 h-12 rounded-full bg-gradient-to-br from-primary-500 to-primary-600 text-white font-bold text-xl flex items-center justify-center mx-auto mb-4 shadow-lg"
              >
                {item.step}
              </motion.div>
              <h3 className="font-semibold mb-2 text-gray-900 dark:text-slate-50">
                {item.title}
              </h3>
              <p className="text-sm text-gray-600 dark:text-slate-400">
                {item.description}
              </p>
            </motion.div>
          ))}
        </div>
      </motion.div>
    </div>
  );
};

export default Dashboard;
