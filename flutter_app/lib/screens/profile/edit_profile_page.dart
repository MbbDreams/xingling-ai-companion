import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../providers/auth_provider.dart';
import '../../utils/theme.dart';

/// 编辑个人资料页面
class EditProfilePage extends ConsumerStatefulWidget {
  const EditProfilePage({super.key});

  @override
  ConsumerState<EditProfilePage> createState() => _EditProfilePageState();
}

class _EditProfilePageState extends ConsumerState<EditProfilePage> {
  final _formKey = GlobalKey<FormState>();
  late TextEditingController _nicknameController;
  late TextEditingController _emailController;
  late TextEditingController _bioController;
  late TextEditingController _locationController;
  late TextEditingController _websiteController;
  
  String? _gender;
  String? _birthday;
  bool _isLoading = false;
  bool _hasChanges = false;

  @override
  void initState() {
    super.initState();
    final user = ref.read(authProvider).user;
    _nicknameController = TextEditingController(text: user?.nickname ?? '');
    _emailController = TextEditingController(text: user?.email ?? '');
    _bioController = TextEditingController(text: user?.bio ?? '');
    _locationController = TextEditingController(text: user?.location ?? '');
    _websiteController = TextEditingController(text: user?.website ?? '');
    _gender = user?.gender;
    _birthday = user?.birthday;

    // 监听变化
    _nicknameController.addListener(_onChanged);
    _emailController.addListener(_onChanged);
    _bioController.addListener(_onChanged);
    _locationController.addListener(_onChanged);
    _websiteController.addListener(_onChanged);
  }

  void _onChanged() {
    if (!_hasChanges) {
      setState(() => _hasChanges = true);
    }
  }

  @override
  void dispose() {
    _nicknameController.dispose();
    _emailController.dispose();
    _bioController.dispose();
    _locationController.dispose();
    _websiteController.dispose();
    super.dispose();
  }

  Future<void> _selectBirthday() async {
    final date = await showDatePicker(
      context: context,
      initialDate: _birthday != null 
          ? DateTime.parse(_birthday!) 
          : DateTime(1990, 1, 1),
      firstDate: DateTime(1950),
      lastDate: DateTime.now(),
      builder: (context, child) {
        return Theme(
          data: Theme.of(context).copyWith(
            colorScheme: const ColorScheme.dark(
              primary: AppTheme.primary,
              surface: Color(0xFF0A0F24),
            ),
          ),
          child: child!,
        );
      },
    );
    
    if (date != null) {
      setState(() {
        _birthday = '${date.year}-${date.month.toString().padLeft(2, '0')}-${date.day.toString().padLeft(2, '0')}';
        _hasChanges = true;
      });
    }
  }

  Future<void> _save() async {
    if (!_formKey.currentState!.validate()) return;

    setState(() => _isLoading = true);

    final success = await ref.read(authProvider.notifier).updateProfile(
      nickname: _nicknameController.text,
      email: _emailController.text.isEmpty ? null : _emailController.text,
      gender: _gender,
      birthday: _birthday,
      bio: _bioController.text.isEmpty ? null : _bioController.text,
      location: _locationController.text.isEmpty ? null : _locationController.text,
      website: _websiteController.text.isEmpty ? null : _websiteController.text,
    );

    if (mounted) {
      setState(() => _isLoading = false);
      if (success) {
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(content: Text('资料已更新'), backgroundColor: AppTheme.primary),
        );
        Navigator.pop(context);
      } else {
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(content: Text('保存失败'), backgroundColor: AppTheme.danger),
        );
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: const Color(0xFF030817),
      appBar: AppBar(
        backgroundColor: Colors.transparent,
        title: const Text('编辑资料', style: TextStyle(color: Colors.white)),
        leading: IconButton(
          icon: const Icon(Icons.close, color: Colors.white),
          onPressed: () => Navigator.pop(context),
        ),
        actions: [
          TextButton(
            onPressed: (_isLoading || !_hasChanges) ? null : _save,
            child: _isLoading
                ? const SizedBox(
                    width: 20,
                    height: 20,
                    child: CircularProgressIndicator(strokeWidth: 2, color: AppTheme.primary),
                  )
                : const Text('保存', style: TextStyle(color: AppTheme.primary, fontWeight: FontWeight.w600)),
          ),
        ],
      ),
      body: Form(
        key: _formKey,
        child: ListView(
          padding: const EdgeInsets.all(16),
          children: [
            // 头像
            Center(
              child: Stack(
                children: [
                  Container(
                    width: 100,
                    height: 100,
                    decoration: BoxDecoration(
                      shape: BoxShape.circle,
                      border: Border.all(color: AppTheme.primary.withOpacity(0.5), width: 2),
                      boxShadow: [
                        BoxShadow(
                          color: AppTheme.primary.withOpacity(0.2),
                          blurRadius: 20,
                        ),
                      ],
                    ),
                    child: const CircleAvatar(
                      radius: 48,
                      backgroundColor: Color(0xFF1A2549),
                      child: Text('🌙', style: TextStyle(fontSize: 40)),
                    ),
                  ),
                  Positioned(
                    bottom: 0,
                    right: 0,
                    child: Container(
                      padding: const EdgeInsets.all(8),
                      decoration: const BoxDecoration(
                        color: AppTheme.primary,
                        shape: BoxShape.circle,
                      ),
                      child: const Icon(Icons.camera_alt, color: Colors.white, size: 16),
                    ),
                  ),
                ],
              ),
            ),
            const SizedBox(height: 32),
            // 昵称
            _buildTextField(
              controller: _nicknameController,
              label: '昵称',
              hint: '你的名字',
              icon: Icons.person_outline,
              validator: (v) => v?.isEmpty == true ? '请输入昵称' : null,
            ),
            const SizedBox(height: 16),
            // 性别
            _buildLabel('性别'),
            const SizedBox(height: 8),
            Row(
              children: [
                _buildGenderChip('male', '👨', '男'),
                const SizedBox(width: 12),
                _buildGenderChip('female', '👩', '女'),
                const SizedBox(width: 12),
                _buildGenderChip('other', '🧑', '其他'),
              ],
            ),
            const SizedBox(height: 16),
            // 生日
            _buildLabel('生日'),
            const SizedBox(height: 8),
            GestureDetector(
              onTap: _selectBirthday,
              child: Container(
                padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 14),
                decoration: BoxDecoration(
                  color: const Color(0x14FFFFFF),
                  borderRadius: BorderRadius.circular(12),
                  border: Border.all(color: AppTheme.line),
                ),
                child: Row(
                  children: [
                    const Icon(Icons.cake_outlined, color: AppTheme.muted),
                    const SizedBox(width: 12),
                    Text(
                      _birthday ?? '选择生日',
                      style: TextStyle(
                        color: _birthday != null ? Colors.white : AppTheme.soft,
                      ),
                    ),
                    const Spacer(),
                    Icon(Icons.chevron_right, color: AppTheme.soft),
                  ],
                ),
              ),
            ),
            const SizedBox(height: 16),
            // 邮箱
            _buildTextField(
              controller: _emailController,
              label: '邮箱',
              hint: 'your@email.com',
              icon: Icons.email_outlined,
              keyboardType: TextInputType.emailAddress,
            ),
            const SizedBox(height: 16),
            // 所在地
            _buildTextField(
              controller: _locationController,
              label: '所在地',
              hint: '你在哪个城市',
              icon: Icons.location_on_outlined,
            ),
            const SizedBox(height: 16),
            // 个人网站
            _buildTextField(
              controller: _websiteController,
              label: '个人网站',
              hint: 'https://yourwebsite.com',
              icon: Icons.language_outlined,
              keyboardType: TextInputType.url,
            ),
            const SizedBox(height: 16),
            // 个人简介
            _buildTextField(
              controller: _bioController,
              label: '个人简介',
              hint: '介绍一下自己...',
              icon: Icons.edit_outlined,
              maxLines: 4,
              maxLength: 200,
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildLabel(String text) {
    return Text(
      text,
      style: const TextStyle(
        color: AppTheme.muted,
        fontSize: 14,
        fontWeight: FontWeight.w500,
      ),
    );
  }

  Widget _buildTextField({
    required TextEditingController controller,
    required String label,
    required String hint,
    required IconData icon,
    int maxLines = 1,
    int? maxLength,
    TextInputType? keyboardType,
    String? Function(String?)? validator,
  }) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        _buildLabel(label),
        const SizedBox(height: 8),
        TextFormField(
          controller: controller,
          style: const TextStyle(color: Colors.white),
          maxLines: maxLines,
          maxLength: maxLength,
          keyboardType: keyboardType,
          validator: validator,
          decoration: InputDecoration(
            hintText: hint,
            hintStyle: TextStyle(color: AppTheme.soft),
            prefixIcon: Icon(icon, color: AppTheme.muted),
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
            counterStyle: TextStyle(color: AppTheme.soft),
          ),
        ),
      ],
    );
  }

  Widget _buildGenderChip(String value, String emoji, String label) {
    final isSelected = _gender == value;
    return GestureDetector(
      onTap: () {
        setState(() {
          _gender = value;
          _hasChanges = true;
        });
      },
      child: Container(
        padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 10),
        decoration: BoxDecoration(
          color: isSelected ? AppTheme.primary.withOpacity(0.3) : const Color(0x14FFFFFF),
          borderRadius: BorderRadius.circular(20),
          border: Border.all(
            color: isSelected ? AppTheme.primary : AppTheme.line,
          ),
        ),
        child: Row(
          mainAxisSize: MainAxisSize.min,
          children: [
            Text(emoji),
            const SizedBox(width: 6),
            Text(
              label,
              style: TextStyle(
                color: isSelected ? Colors.white : AppTheme.muted,
              ),
            ),
          ],
        ),
      ),
    );
  }
}
