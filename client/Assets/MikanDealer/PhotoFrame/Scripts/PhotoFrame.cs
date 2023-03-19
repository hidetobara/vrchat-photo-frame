
using UdonSharp;
using UnityEngine;
using VRC.SDK3.Image;
using VRC.SDKBase;
using VRC.Udon;
using VRC.Udon.Common.Interfaces;

public class PhotoFrame : UdonSharpBehaviour
{
	public string Name;
	public bool AutoAdjust = true;
	public float FrameWidth = 0.1f;
	[HideInInspector]
	public VRCUrl Url;

	void Start()
	{
		var renderer = GetComponent<MeshRenderer>();
		if (renderer != null && !string.IsNullOrEmpty(Url.Get()) && renderer.material != null)
		{
			var downloader = new VRCImageDownloader();
			downloader.DownloadImage(Url, renderer.sharedMaterial, (IUdonEventReceiver)this);
		}
	}

	override public void OnImageLoadSuccess(IVRCImageDownload download)
	{
		if (AutoAdjust && download.Result != null)
		{
			AdjustTexture(download.Result);
		}
	}

	public void AdjustTexture(Texture2D tex)
	{
		float baseScale = 1;
		Vector3 scale;
		if (gameObject.transform.localScale.x > baseScale) baseScale = gameObject.transform.localScale.x;
		if (gameObject.transform.localScale.y > baseScale) baseScale = gameObject.transform.localScale.y;
		if (gameObject.transform.localScale.z > baseScale) baseScale = gameObject.transform.localScale.z;

		if (tex.height > tex.width)
		{
			scale = new Vector3((float)tex.width / (float)tex.height, 1, 1);
		}
		else
		{
			scale = new Vector3(1, (float)tex.height / (float)tex.width, 1);
		}
		gameObject.transform.localScale = scale * baseScale;

		var renderer = GetComponent<MeshRenderer>();
		if (renderer != null)
		{
			renderer.sharedMaterial.SetFloat("_ScaleX", 1 + scale.y * FrameWidth);
			renderer.sharedMaterial.SetFloat("_ScaleY", 1 + scale.x * FrameWidth);
		}
	}
}
