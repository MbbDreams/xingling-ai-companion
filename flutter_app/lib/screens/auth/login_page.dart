import 'dart:async';
import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../providers/auth_provider.dart';
import '../../utils/theme.dart';
import 'register_page.dart';

/// 登录页面
class LoginPage extends ConsumerStatefulWidget {
  const LoginPage({super.key});

  @override
  ConsumerState<LoginPage> createState() => _LoginPageState();
}

class _LoginPageState extends ConsumerState<LoginPage> {
  final _phoneController = TextEditingController();
  final _codeController = TextEditingController();
  final _formKey = GlobalKey<FormState>();
  
  bool _isLoading = false;
  bool _codeSent = false;
  int _countdown = 0;
  Timer? _countdownTimer;
  String? _error;

  @override
  void dispose() {
    _phoneController.dispose();
    _codeController.dispose();
    _countdownTimer?.cancel();
    super.dispose();
  }

  void _startCountdown() {
    _countdown = 60;
    _countdownTimer?.cancel();
    _countdownTimer = Timer.periodic(const Duration(seconds: 1), (timer) {
      if (mounted) {
        setState(() {
          _countdown--;
          if (_countdown <= 0) {
            timer.cancel();
          }
        });
      }
    });
  }

  Future<void> _sendCode() async {
    // 手动验证手机号
    final phone = _phoneController.text.trim();
    if (phone.length != 11) {
      setState(() {
        _error = '请输入正确的11位手机号';
      });
      return;
    }

    setState(() {
      _isLoading = true;
      _error = null;
    });

    try {
      final success = await ref.read(authProvider.notifier).sendCode(phone);

      if (mounted) {
        setState(() {
          _isLoading = false;
          if (success) {
            _codeSent = true;
            _startCountdown();
          } else {
            _error = '验证码发送失败，请检查网络或稍后重试';
          }
        });
      }
    } catch (e) {
      if (mounted) {
        setState(() {
          _isLoading = false;
          _error = '网络错误: $e';
        });
      }
    }
  }

  Future<void> _login() async {
    if (!_formKey.currentState!.validate()) return;

    setState(() {
      _isLoading = true;
      _error = null;
    });

    final success = await ref.read(authProvider.notifier).login(
      phone: _phoneController.text,
      code: _codeController.text,
    );

    if (mounted) {
      setState(() {
        _isLoading = false;
        if (!success) {
          _error = '验证码错误或已过期';
        }
      });
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: const Color(0xFF030817),
      body: SafeArea(
        child: SingleChildScrollView(
          padding: const EdgeInsets.all(24),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              const SizedBox(height: 60),
              // Logo和标题
              Center(
                child: Column(
                  children: [
                    Container(
                      width: 80,
                      height: 80,
                      decoration: BoxDecoration(
                        shape: BoxShape.circle,
                        gradient: const LinearGradient(
                          colors: [Color(0xFF8F73FF), Color(0xFF5E6AD3)],
                        ),
                        boxShadow: [
                          BoxShadow(
                            color: const Color(0xFF8F73FF).withOpacity(0.3),
                            blurRadius: 30,
                          ),
                        ],
                      ),
                      alignment: Alignment.center,
                      child: const Text('🌙', style: TextStyle(fontSize: 40)),
                    ),
                    const SizedBox(height: 20),
                    const Text(
                      '星灵',
                      style: TextStyle(
                        fontSize: 32,
                        fontWeight: FontWeight.w800,
                        color: Colors.white,
                      ),
                    ),
                    const SizedBox(height: 4),
                    Text(
                      '你的AI灵魂伴侣',
                      style: TextStyle(
                        fontSize: 16,
                        color: AppTheme.muted,
                      ),
                    ),
                  ],
                ),
              ),
              const SizedBox(height: 60),
              // 表单
              Form(
                key: _formKey,
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    const Text(
                      '手机号登录',
                      style: TextStyle(
                        fontSize: 20,
                        fontWeight: FontWeight.w700,
                        color: Colors.white,
                      ),
                    ),
                    const SizedBox(height: 8),
                    Text(
                      '未注册的手机号将自动注册',
                      style: TextStyle(color: AppTheme.muted),
                    ),
                    const SizedBox(height: 24),
                    // 手机号输入
                    TextFormField(
                      controller: _phoneController,
                      keyboardType: TextInputType.phone,
                      style: const TextStyle(color: Colors.white),
                      decoration: InputDecoration(
                        labelText: '手机号',
                        labelStyle: const TextStyle(color: AppTheme.muted),
                        hintText: '请输入手机号',
                        hintStyle: TextStyle(color: AppTheme.soft),
                        prefixIcon: const Icon(Icons.phone_outlined, color: AppTheme.muted),
                        filled: true,
                        fillColor: const Color(0x14FFFFFF),
                        border: OutlineInputBorder(
                          borderRadius: BorderRadius.circular(12),
                          borderSide: BorderSide(color: AppTheme.line),
                        ),
                        enabledBorder: OutlineInputBorder(
                          borderRadius: BorderRadius.circular(12),
                          borderSide: BorderSide(color: AppTheme.line),
                        ),
                        focusedBorder: OutlineInputBorder(
                          borderRadius: BorderRadius.circular(12),
                          borderSide: const BorderSide(color: AppTheme.primary),
                        ),
                      ),
                      inputFormatters: [
                        FilteringTextInputFormatter.digitsOnly,
                        LengthLimitingTextInputFormatter(11),
                      ],
                      validator: (value) {
                        if (value == null || value.length != 11) {
                          return '请输入正确的手机号';
                        }
                        return null;
                      },
                    ),
                    const SizedBox(height: 16),
                    // 验证码输入
                    TextFormField(
                      controller: _codeController,
                      keyboardType: TextInputType.number,
                      style: const TextStyle(color: Colors.white),
                      enabled: _codeSent,
                      decoration: InputDecoration(
                        labelText: '验证码',
                        labelStyle: TextStyle(color: _codeSent ? AppTheme.muted : AppTheme.soft),
                        hintText: '请输入验证码',
                        hintStyle: TextStyle(color: AppTheme.soft),
                        prefixIcon: Icon(Icons.lock_outlined, color: _codeSent ? AppTheme.muted : AppTheme.soft),
                        filled: true,
                        fillColor: const Color(0x14FFFFFF),
                        border: OutlineInputBorder(
                          borderRadius: BorderRadius.circular(12),
                          borderSide: BorderSide(color: AppTheme.line),
                        ),
                        enabledBorder: OutlineInputBorder(
                          borderRadius: BorderRadius.circular(12),
                          borderSide: BorderSide(color: AppTheme.line),
                        ),
                        focusedBorder: OutlineInputBorder(
                          borderRadius: BorderRadius.circular(12),
                          borderSide: const BorderSide(color: AppTheme.primary),
                        ),
                      ),
                      inputFormatters: [
                        FilteringTextInputFormatter.digitsOnly,
                        LengthLimitingTextInputFormatter(6),
                      ],
                      validator: (value) {
                        if (value == null || value.length != 6) {
                          return '请输入6位验证码';
                        }
                        return null;
                      },
                    ),
                    const SizedBox(height: 16),
                    // 发送验证码按钮
                    SizedBox(
                      width: double.infinity,
                      height: 48,
                      child: _countdown > 0
                          ? Container(
                              decoration: BoxDecoration(
                                color: const Color(0x14FFFFFF),
                                borderRadius: BorderRadius.circular(24),
                                border: Border.all(color: AppTheme.line),
                              ),
                              alignment: Alignment.center,
                              child: Text(
                                '${_countdown}秒后可重发',
                                style: TextStyle(color: AppTheme.muted, fontSize: 15),
                              ),
                            )
                          : GestureDetector(
                              onTap: _isLoading ? null : _sendCode,
                              child: Container(
                                decoration: BoxDecoration(
                                  color: AppTheme.primary.withOpacity(0.15),
                                  borderRadius: BorderRadius.circular(24),
                                  border: Border.all(color: AppTheme.primary.withOpacity(0.5)),
                                ),
                                alignment: Alignment.center,
                                child: _isLoading
                                    ? const SizedBox(
                                        width: 20,
                                        height: 20,
                                        child: CircularProgressIndicator(
                                          strokeWidth: 2,
                                          valueColor: AlwaysStoppedAnimation<Color>(AppTheme.primary),
                                        ),
                                      )
                                    : Text(
                                        _codeSent ? '重新发送验证码' : '发送验证码',
                                        style: const TextStyle(
                                          color: AppTheme.primary,
                                          fontSize: 15,
                                          fontWeight: FontWeight.w600,
                                        ),
                                      ),
                              ),
                            ),
                    ),
                    const SizedBox(height: 24),
                    // 错误提示
                    if (_error != null)
                      Container(
                        padding: const EdgeInsets.all(12),
                        decoration: BoxDecoration(
                          color: AppTheme.danger.withOpacity(0.1),
                          borderRadius: BorderRadius.circular(8),
                        ),
                        child: Row(
                          children: [
                            const Icon(Icons.error_outline, color: AppTheme.danger, size: 18),
                            const SizedBox(width: 8),
                            Expanded(
                              child: Text(
                                _error!,
                                style: const TextStyle(color: AppTheme.danger, fontSize: 13),
                              ),
                            ),
                          ],
                        ),
                      ),
                    const SizedBox(height: 24),
                    // 登录按钮
                    SizedBox(
                      width: double.infinity,
                      height: 52,
                      child: Container(
                        decoration: BoxDecoration(
                          gradient: const LinearGradient(
                            colors: [Color(0xFF8F73FF), Color(0xFF5E6AD3)],
                          ),
                          borderRadius: BorderRadius.circular(26),
                          boxShadow: [
                            BoxShadow(
                              color: const Color(0xFF8F73FF).withOpacity(0.3),
                              blurRadius: 20,
                              offset: const Offset(0, 4),
                            ),
                          ],
                        ),
                        child: ElevatedButton(
                          onPressed: (_isLoading || !_codeSent) ? null : _login,
                          style: ElevatedButton.styleFrom(
                            backgroundColor: Colors.transparent,
                            shadowColor: Colors.transparent,
                            shape: RoundedRectangleBorder(
                              borderRadius: BorderRadius.circular(26),
                            ),
                          ),
                          child: _isLoading
                              ? const SizedBox(
                                  width: 24,
                                  height: 24,
                                  child: CircularProgressIndicator(
                                    strokeWidth: 2,
                                    valueColor: AlwaysStoppedAnimation<Color>(Colors.white),
                                  ),
                                )
                              : const Text(
                                  '登录 / 注册',
                                  style: TextStyle(
                                    fontSize: 16,
                                    fontWeight: FontWeight.w600,
                                    color: Colors.white,
                                  ),
                                ),
                        ),
                      ),
                    ),
                  ],
                ),
              ),
              const SizedBox(height: 40),
              // 隐私协议提示
              Center(
                child: Text(
                  '登录即表示同意《用户协议》和《隐私政策》',
                  style: TextStyle(fontSize: 11, color: AppTheme.soft),
                  textAlign: TextAlign.center,
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }
}
